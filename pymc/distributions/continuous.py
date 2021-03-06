"""
pymc.distributions

A collection of common probability distributions for stochastic
nodes in PyMC.

"""
from __future__ import division

from dist_math import *
from numpy.random import uniform as runiform, normal as rnormal

__all__ = ['Uniform', 'Flat', 'Normal', 'Beta', 'Exponential', 'Laplace',
           'T', 'Cauchy', 'Gamma', 'Bound', 'Tpos', 'Lognormal']

def get_tau(tau=None, sd=None):
    if tau is None:
        if sd is None:
            return 1.
        else:
            return sd ** -2

    else:
        if sd is not None:
            raise ValueError("Can't pass both tau and sd")
        else:
            return tau

@tensordist(continuous)
def Uniform(lower=0, upper=1):
    """
    Continuous uniform log-likelihood.

    .. math::
        f(x \mid lower, upper) = \frac{1}{upper-lower}

    Parameters
    ----------
    lower : float
        Lower limit (defaults to 0)
    upper : float
        Upper limit (defaults to 1)
    """

    def logp(value):
        return bound(
            -log(upper - lower),
            lower <= value, value <= upper)

    def random(size=None):
        return runiform(upper, lower, size)

    mean = (upper + lower) / 2.
    median = mean

    logp.__doc__ = """
        Uniform log-likelihood with parameters lower={0} and upper={1}.

        Parameters
        ----------
        value : float
            :math:`lower \leq x \leq upper`
        """

    return locals()


@tensordist(continuous)
def Flat():
    """
    Uninformative log-likelihood that returns 0 regardless of
    the passed value.
    """

    def logp(value):
        return zeros_like(value)

    logp.__doc__ = """
        Uninformative log-likelihood that returns 0 regardless of
        the passed value.
        """

    median = 0

    return locals()


@tensordist(continuous)
def Normal(mu=0.0, tau=None, sd=None):
    """
    Normal log-likelihood.

    .. math::
        f(x \mid \mu, \tau) = \sqrt{\frac{\tau}{2\pi}} \exp\left\{ -\frac{\tau}{2} (x-\mu)^2 \right\}

    Parameters
    ----------
    mu : float
        Mean of the distribution.
    tau : float
        Precision of the distribution, which corresponds to
        :math:`1/\sigma^2` (tau > 0).
    sd : float
        Standard deviation of the distribution. Alternative parameterization.

    .. note::
    - :math:`E(X) = \mu`
    - :math:`Var(X) = 1/\tau`

    """

    tau = get_tau(tau=tau, sd=sd)

    def logp(value):

        return bound(
            (-tau * (value - mu) ** 2 + log(tau / pi / 2.)) / 2.,
            tau > 0)

    mean = mu
    variance = 1. / tau

    median = mean
    mode = mean

    logp.__doc__ = """
        Normal log-likelihood with parameters mu={0} and tau={1}.

        Parameters
        ----------
        value : float
            Input data.
        """.format(mu, tau)

    return locals()

@tensordist(continuous)
def Beta(alpha, beta):
    """
    Beta log-likelihood. The conjugate prior for the parameter
    :math:`p` of the binomial distribution.

    .. math::
        f(x \mid \alpha, \beta) = \frac{\Gamma(\alpha + \beta)}{\Gamma(\alpha) \Gamma(\beta)} x^{\alpha - 1} (1 - x)^{\beta - 1}

    Parameters
    ----------
    alpha : float
        alpha > 0
    beta : float
        beta > 0

    .. note::
    - :math:`E(X)=\frac{\alpha}{\alpha+\beta}`
    - :math:`Var(X)=\frac{\alpha \beta}{(\alpha+\beta)^2(\alpha+\beta+1)}`

    """
    def logp(value):

        return bound(
            gammaln(alpha + beta) - gammaln(alpha) - gammaln(beta) +
            logpow(
                value, alpha - 1) + logpow(1 - value, beta - 1),
            0 <= value, value <= 1,
            alpha > 0,
            beta > 0)

    mean = alpha / (alpha + beta)
    variance = alpha * beta / (
        (alpha + beta) ** 2 * (alpha + beta + 1))

    logp.__doc__ = """
    Beta log-likelihood with parameters alpha={0} and beta={1}.

    Parameters
    ----------
    value : float
        0 < x < 1
    """.format(alpha, beta)

    return locals()


@tensordist(continuous)
def Exponential(lam):
    """
    Exponential distribution

    Parameters
    ----------
    lam : float
        lam > 0
        rate or inverse scale
    """

    mean = 1. / lam
    median = mean * log(2)
    mode = 0

    variance = lam ** -2

    def logp(value):
        return bound(log(lam) - lam * value,
                     value > 0,
                     lam > 0)

    return locals()


@tensordist(continuous)
def Laplace(mu, b):
    """
    Laplace distribution

    Parameters
    ----------
    mu : float
        mean
    b : float
        scale
    """

    mean = median = mode = mu

    variance = 2 * b ** 2

    def logp(value):
        return -log(2 * b) - abs(value - mu) / b

    return locals()


@tensordist(continuous)
def Lognormal(mu=0, tau=1):
    """
    Log-normal log-likelihood.

    Distribution of any random variable whose logarithm is normally
    distributed. A variable might be modeled as log-normal if it can
    be thought of as the multiplicative product of many small
    independent factors.

    .. math::
        f(x \mid \mu, \tau) = \sqrt{\frac{\tau}{2\pi}}\frac{
        \exp\left\{ -\frac{\tau}{2} (\ln(x)-\mu)^2 \right\}}{x}

    :Parameters:
      - `x` : x > 0
      - `mu` : Location parameter.
      - `tau` : Scale parameter (tau > 0).

    .. note::

       :math:`E(X)=e^{\mu+\frac{1}{2\tau}}`
       :math:`Var(X)=(e^{1/\tau}-1)e^{2\mu+\frac{1}{\tau}}`

    """
    def logp(value):
        return bound(
            -0.5*tau*(log(value) - mu)**2 + 0.5*log(tau/(2.*pi)) - log(value),
            tau > 0)

    mean = exp(mu + 1./(2*tau))
    median = exp(mu)
    mode = exp(mu - 1./tau)

    variance = (exp(1./tau) - 1) * exp(2*mu + 1./tau)

    logp.__doc__ = """
        Log-normal log-likelihood with paramters mu={0} and tau={1}.

        Parameters
        ----------
        value : float
            Input data
        """

    return locals()


@tensordist(continuous)
def T(nu, mu=0, lam=1):
    """
    Non-central Student's T log-likelihood.

    Describes a normal variable whose precision is gamma distributed. If
    only nu parameter is passed, this specifies a standard (central)
    Student's T.

    .. math::
        f(x|\mu,\lambda,\nu) = \frac{\Gamma(\frac{\nu +
        1}{2})}{\Gamma(\frac{\nu}{2})}
        \left(\frac{\lambda}{\pi\nu}\right)^{\frac{1}{2}}
        \left[1+\frac{\lambda(x-\mu)^2}{\nu}\right]^{-\frac{\nu+1}{2}}

    Parameters
    ----------
    nu : int
        Degrees of freedom
    mu : float
        Location parameter (defaults to 0)
    lam : float
        Scale parameter (defaults to 1)
    """

    def logp(value):
        return bound(
            gammaln((nu + 1.0) / 2.0) + .5 * log(lam / (nu * pi)) - gammaln(nu / 2.0) - (nu + 1.0) / 2.0 * log(1.0 + lam * (value - mu) ** 2 / nu),
            lam > 0,
            nu > 0)

    mean = mu
    median = mu
    mode = mu

    variance = switch((nu > 2) * 1, nu / (nu - 2) / lam, inf)

    logp.__doc__ = """
        Student's T log-likelihood with paramters nu={0}, mu={1} and lam={2}.

        Parameters
        ----------
        value : float
            Input data
        """

    return locals()


@tensordist(continuous)
def Cauchy(alpha, beta):
    """
    Cauchy log-likelihood. The Cauchy distribution is also known as the
    Lorentz or the Breit-Wigner distribution.

    .. math::
        f(x \mid \alpha, \beta) = \frac{1}{\pi \beta [1 + (\frac{x-\alpha}{\beta})^2]}

    Parameters
    ----------
    alpha : float
        Location parameter
    beta : float
        Scale parameter > 0

    .. note::
    Mode and median are at alpha.

    """

    median = mode = alpha

    def logp(value):
        return bound(
            -log(pi) - log(beta) - log(1 + ((
                                            value - alpha) / beta) ** 2),
            beta > 0)

    logp.__doc__ = """
        Cauchy log-likelihood with parameters alpha={0} and beta={0}.

        Parameters
        ----------
        value : float
            Input data.
        """.format(alpha, beta)
    return locals()


@tensordist(continuous)
def Gamma(alpha, beta):
    """
    Gamma log-likelihood.

    Represents the sum of alpha exponentially distributed random variables, each
    of which has mean beta.

    .. math::
        f(x \mid \alpha, \beta) = \frac{\beta^{\alpha}x^{\alpha-1}e^{-\beta x}}{\Gamma(\alpha)}

    Parameters
    ----------
    x : float
        math:`x \ge 0`
    alpha : float
        Shape parameter (alpha > 0).
    beta : float
        Rate parameter (beta > 0).

    .. note::
    - :math:`E(X) = \frac{\alpha}{\beta}`
    - :math:`Var(X) = \frac{\alpha}{\beta^2}`

    """

    mean = alpha / beta
    median = maximum((alpha - 1) / beta, 0)
    variance = alpha / beta ** 2

    def logp(value):
        return bound(
            -gammaln(alpha) + logpow(
                beta, alpha) - beta * value + logpow(value, alpha - 1),

            value >= 0,
            alpha > 0,
            beta > 0)

    logp.__doc__ = """
        Gamma log-likelihood with paramters alpha={0} and beta={1}.

        Parameters
        ----------
        x : float
            math:`x \ge 0`
        """.format(alpha, beta)

    return locals()


def Bound(distribution, lower=-inf, upper=inf):
    @tensordist(continuous)
    @wraps_with_spec(distribution)
    def Bounded(*args, **kwargs):
        """A bounded distribution."""
        dist = distribution.dist(*args, **kwargs)

        def logp(value):
            return bound(
                dist.logp(value),

                lower <= value, value <= upper)

        if hasattr(dist,'mode'):
            mode = dist.mode

        return locals()
    return Bounded


Tpos = Bound(T, 0)

