# Network impact engineering reference

This problem uses a static undirected multigraph with several active cores. Each cable is an independently fail-able edge. Add a synthetic source connected to all cores, then compute bridge properties and weighted subtree sums. A physical edge separates newly disconnected sites only if its removal cuts all paths to the synthetic source. Components that started without core service contribute zero. Keep physical cable identities distinct, including links between identical pairs of sites.

The indexing pass can run in time proportional to the number of sites and links, and subsequent impact queries can use precomputed answers. Ranked queries can use a prepared ordering. Avoid repeated full-network traversals, incorrect handling of parallel links, and recursion depth failures on long chains. Subtree weights count access sites, active accounts, and priority accounts, not intermediate exchanges.

S-06 affects A-2 and A-3, totaling two sites, 150 active accounts, and 39 priority accounts. S-12 affects one site, 70 accounts and 35 priority accounts. S-11 affects one, 55 and 20. S-07 affects one, 110 and 9. S-09 affects one, 25 and 5. S-10 affects one location with zero accounts. The expected top five are S-06, S-12, S-11, S-07, and S-09.

Compare outcomes against a slow reference on small random networks. Exercise distinct parallel links, several cores, a loop, an unserved island, an access site with zero subscribers, disabled links, malformed requests, and deterministic sorting. Production feasibility at millions of vertices requires compact indexing and careful memory profiling rather than speculative latency guarantees.
