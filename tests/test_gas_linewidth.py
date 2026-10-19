"""Gas-cavity loss term (modelling assumption GAS_Q): gas modes have a non-zero linewidth that enters the lock rule."""
import solver_v0 as S


def test_gas_q_is_named_and_finite():
    assert S.GAS_Q == 3000.0
    assert abs(S.gas_linewidth(1.0e6) - 1.0e6 / 3000.0) < 1e-9


def test_gas_linewidth_widens_the_lock_window():
    fq, Qq = 1.0e6, 2100.0                 # quartz mode: FWHM 476.2 Hz -> half 238.1 Hz on its own
    lwq, lwg = fq / Qq, S.gas_linewidth(fq)  # gas FWHM 333.3 Hz -> combined half-width 404.8 Hz
    df = 300.0
    assert not S.modes_lock(fq, lwq, fq + df, 0.0)       # zero-loss gas: outside half the partner's width
    assert S.modes_lock(fq, lwq, fq + df, lwg)           # with its own linewidth: inside half the sum
    assert not S.modes_lock(fq, lwq, fq + 410.0, lwg)
    assert S.modes_lock(fq, lwq, fq + 0.5 * (lwq + lwg), lwg)   # boundary is inclusive (<=)
