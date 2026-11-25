# Optimal blackjack bot vs dealer bot. Exact composition-dependent EV (with-replacement approx) for every decision,
# exact pre-deal edge -> fractional Kelly bets, wong out at negative edge, exact insurance.
# Rules: 6D, S17, peek, 3:2, DAS, LS, split once, split aces get 1 card.
import random, sys, argparse
from functools import lru_cache
R = range(1, 11)
def best(t, a): return t + 10 if a and t <= 11 else t

class Ctx:
    def __init__(s, q): s.q, s.dm, s.tc = q, {}, {}
    def d(s, t, a):
        k = (t, a)
        if k in s.dm: return s.dm[k]
        b, r = best(t, a), [0.0] * 6
        if b > 21: r[5] = 1
        elif b >= 17: r[b - 17] = 1
        else:
            for c in R:
                if s.q[c]:
                    x = s.d(t + c, a or c == 1)
                    for i in range(6): r[i] += s.q[c] * x[i]
        s.dm[k] = r; return r
    def t(s, u):
        if u not in s.tc: s.tc[u] = T(s, u)
        return s.tc[u]

class T:
    def __init__(s, c, u):
        q = s.q = c.q; s.bj = 10 if u == 1 else 1 if u == 10 else 0
        z = 1 - (q[s.bj] if s.bj else 0); D = [0.0] * 6
        for h in R:
            if h != s.bj and q[h] and z > 0:
                x = c.d(u + h, u == 1 or h == 1)
                for i in range(6): D[i] += q[h] / z * x[i]
        s.D, s.H, s.Dd, s.Sp = D, {}, {}, {}
    def S(s, t, a):
        b, D = best(t, a), s.D
        if b > 21: return -1.0
        if b < 17: return 2 * D[5] - 1
        i = b - 17; return D[5] + sum(D[:i]) - sum(D[i + 1:5])
    def h(s, t, a):
        k = (t, a)
        if k not in s.H: s.H[k] = sum(s.q[c] * (-1.0 if t + c > 21 else max(s.S(t + c, a or c == 1), s.h(t + c, a or c == 1))) for c in R)
        return s.H[k]
    def dbl(s, t, a):
        k = (t, a)
        if k not in s.Dd: s.Dd[k] = 2 * sum(s.q[c] * s.S(t + c, a or c == 1) for c in R)
        return s.Dd[k]
    def sp(s, c):
        if c not in s.Sp:
            q = s.q
            s.Sp[c] = 2 * sum(q[x] * s.S(1 + x, True) for x in R) if c == 1 else \
                2 * sum(q[x] * max(s.S(c + x, x == 1), s.h(c + x, x == 1), s.dbl(c + x, x == 1)) for x in R)
        return s.Sp[c]
    def opts(s, cards, first, can_dbl, can_split):
        t, a = sum(cards), 1 in cards
        o = {'S': s.S(t, a), 'H': s.h(t, a)}
        if len(cards) == 2:
            if can_dbl: o['D'] = s.dbl(t, a)
            if first: o['R'] = -0.5
            if first and can_split and cards[0] == cards[1]: o['P'] = s.sp(cards[0])
        return o

@lru_cache(maxsize=256)
def ctx(cnt):
    n = sum(cnt); return Ctx([x / n for x in cnt])

def edge(cnt):
    c = ctx(cnt); q = c.q; e = 0.0; pnat = 2 * q[1] * q[10]
    for u in R:
        if not q[u]: continue
        t = c.t(u); pbj = q[t.bj] if t.bj else 0; s = 0.0
        for c1 in R:
            for c2 in range(c1, 11):
                pp = q[c1] * q[c2] * (1 if c1 == c2 else 2)
                if pp: s += pp * (1.5 if (c1, c2) == (1, 10) else max(t.opts([c1, c2], 1, 1, 1).values()))
        e += q[u] * (-pbj * (1 - pnat) + (1 - pbj) * s)
    return e + q[1] * max(0.0, 0.5 * (3 * q[10] - 1))

class Shoe:
    def __init__(s, rng, decks=6, pen=0.75, inf=False):
        s.rng, s.n, s.pen, s.inf = rng, decks, pen, inf; s.shuffle()
    def shuffle(s):
        s.cnt = [0] + [4 * s.n] * 9 + [16 * s.n]
        s.cards = [c for c in R for _ in range(s.cnt[c])]; s.rng.shuffle(s.cards); s.cut = int(len(s.cards) * (1 - s.pen))
    def need(s): return not s.inf and len(s.cards) <= s.cut
    def draw(s, seen=True):
        if s.inf: return s.rng.choices(range(11), s.cnt)[0]
        c = s.cards.pop()
        if seen: s.cnt[c] -= 1
        return c
    def reveal(s, c):
        if not s.inf: s.cnt[c] -= 1
    def key(s): return tuple(s.cnt)

def play(sh, bet, free):
    """Returns net result. free = bankroll available for doubles/splits/insurance beyond bet."""
    p = [sh.draw()]; u = sh.draw(); p.append(sh.draw()); hole = sh.draw(False)
    net = 0.0
    if u == 1 and bet and sh.cnt[10] * 3 > sum(sh.cnt) and free >= bet / 2:  # exact: hole card still in unseen count
        ins = bet / 2; free -= ins; net += 2 * ins if hole == 10 else -ins
    dbj = (u == 1 and hole == 10) or (u == 10 and hole == 1); pbj = sorted(p) == [1, 10]
    if dbj or pbj:
        sh.reveal(hole); return net + (0 if dbj and pbj else -bet if dbj else 1.5 * bet)
    done, todo = [], [(p, bet, True, False)]  # todo: (cards, stake, first, split-ace); done: (cards, stake, surrendered)
    while todo:
        cards, b, first, ace = todo.pop(0); sur = False
        if len(cards) == 1: cards.append(sh.draw())
        while not ace and best(sum(cards), 1 in cards) < 21:
            o = ctx(sh.key()).t(u).opts(cards, first, free >= b, free >= b)
            m = max(o, key=o.get)
            if m == 'S': break
            if m == 'R': sur = True; break
            if m == 'H': cards.append(sh.draw()); continue
            if m == 'D': free -= b; b *= 2; cards.append(sh.draw()); break
            free -= b; ace = cards[0] == 1; first = False  # 'P'
            todo.append(([cards[1]], b, False, ace)); cards = [cards[0], sh.draw()]
        done.append((cards, b, sur))
    sh.reveal(hole); dh = [u, hole]
    if any(not r and best(sum(c), 1 in c) <= 21 for c, _, r in done):
        while best(sum(dh), 1 in dh) < 17: dh.append(sh.draw())
    db = best(sum(dh), 1 in dh)
    for c, b, r in done:
        pb = best(sum(c), 1 in c)
        net += -b / 2 if r else -b if pb > 21 else b if db > 21 or pb > db else -b if pb < db else 0
    return net

def session(rounds, bank, mn, mx, kelly, wong, decks, pen, seed, verbose=False):
    rng = random.Random(seed); sh = Shoe(rng, decks, pen); start = bank; wag = played = 0; peak = bank; mdd = 0
    for i in range(rounds):
        if sh.need(): sh.shuffle()
        if bank < mn: break
        e = edge(sh.key())
        bet = (min(mx, max(mn, int(kelly * e / 1.33 * bank))) if e > 0 else 0 if wong else mn)
        bet = min(bet, bank)
        net = play(sh, bet, bank - bet)
        bank += net; wag += bet; played += bet > 0; peak = max(peak, bank); mdd = max(mdd, peak - bank)
        if verbose and bet: print(f"{i} edge={e:+.4f} bet={bet} net={net:+.1f} bank={bank:.1f}")
    print(f"rounds={i + 1} hands_bet={played} wagered={wag:.0f} start={start} final={bank:.2f} "
          f"profit={bank - start:+.2f} roi={(bank - start) / max(wag, 1):+.4%} max_drawdown={mdd:.2f}")
    return bank

def selftest(n):
    full = (0,) + (24,) * 9 + (96,); c = ctx(full)
    ex = {((10, 6), 10): 'R', ((9, 6), 10): 'R', ((10, 6), 9): 'R', ((10, 2), 2): 'H', ((10, 2), 3): 'H', ((10, 2), 4): 'S',
          ((10, 3), 2): 'S', ((10, 6), 7): 'H', ((10, 7), 1): 'S', ((6, 4), 10): 'H', ((5, 4), 2): 'H', ((5, 4), 3): 'D',
          ((5, 3), 6): 'H', ((1, 7), 2): 'S', ((1, 7), 9): 'H', ((1, 7), 3): 'D', ((1, 8), 6): 'S', ((1, 2), 5): 'D',
          ((1, 2), 4): 'H', ((8, 8), 10): 'P', ((8, 8), 1): 'P', ((9, 9), 7): 'S', ((9, 9), 8): 'P', ((10, 10), 6): 'S',
          ((5, 5), 9): 'D', ((4, 4), 5): 'P', ((1, 1), 10): 'P', ((7, 7), 8): 'H', ((6, 5), 10): 'D', ((7, 5), 6): 'S'}
    bad = 0
    for (cards, u), want in ex.items():
        k = list(full)
        for x in cards + (u,): k[x] -= 1  # same as live play: seen cards removed
        o = ctx(tuple(k)).t(u).opts(list(cards), 1, 1, 1); got = max(o, key=o.get)
        if got != want: bad += 1; print("MISMATCH", cards, u, want, got, o)
    print(f"check1 strategy: {len(ex) - bad}/{len(ex)} match basic strategy")
    e = edge(full); print(f"check2 full-shoe edge={e:+.5f} (expect about -0.004..-0.006)")
    rng = random.Random(1); sh = Shoe(rng, inf=True); s = s2 = 0.0
    for _ in range(n): x = play(sh, 1, 10); s += x; s2 += x * x
    m = s / n; se = ((s2 / n - m * m) / n) ** .5
    print(f"check3 monte-carlo engine EV={m:+.5f} +/- {se:.5f} ({n} hands), z={(m - e) / se:+.2f} vs analytic")
    assert bad == 0 and -0.007 < e < -0.003 and abs(m - e) < 3.5 * se

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=20000); ap.add_argument("--bank", type=float, default=10000)
    ap.add_argument("--min", type=float, default=10); ap.add_argument("--max", type=float, default=1000)
    ap.add_argument("--kelly", type=float, default=0.5); ap.add_argument("--no-wong", action="store_true")
    ap.add_argument("--decks", type=int, default=6); ap.add_argument("--pen", type=float, default=0.75)
    ap.add_argument("--seed", type=int); ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--test", type=int, metavar="HANDS")
    a = ap.parse_args()
    if a.test: selftest(a.test)
    else: session(a.rounds, a.bank, a.min, a.max, a.kelly, not a.no_wong, a.decks, a.pen, a.seed, a.verbose)
