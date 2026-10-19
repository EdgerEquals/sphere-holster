I can’t do the thing you’re testing: this chat session has no browser/network/GitHub access, so I can’t fetch `github.com/EdgerEquals/stratified-sphere-model`, inspect the data, or verify that the repo is reachable. I won’t pretend I did.

Because of that, I also can’t responsibly give you a specific “fix these bugs” list. Anything concrete would be invented. To do a real review, I’d need the repo contents pasted/attached, or at minimum: README, directory tree, data schema/sample rows, main code entry points, tests, and any notebook/figure you care about.

What I’d check first, once I can see it:

- **Reproducibility:** pinned dependencies, data download or checksum instructions, no hidden local paths, one-command setup.
- **Data contract:** coordinate convention—lat/lon vs x/y/z, degrees vs radians, axis order, sphere radius, units, missing values, stratification rules.
- **Geometric correctness:** do strata cover the sphere without gaps/overlaps? How are poles, dateline, and cell boundaries handled? Are area weights correct?
- **Invariants and tests:** partition invariants, round-trip tests, known simple geometries, edge-case tests, golden datasets.
- **Performance:** vectorization, spatial indexing, memory use at high resolution, caching of expensive strata.
- **Docs/visualization:** a clear model spec, data dictionary, example figures showing strata, and a minimal usage example.
- **Packaging/licensing/citation:** install path, license, and how to cite the model.

In my own words, based only on the name and your prompt: I think you’re trying to represent a sphere as a **stratified/partitioned structure**—layers, bands, shells, or hierarchical spherical cells—so that spherical data can be indexed, sampled, aggregated, visualized, or analyzed without breaking at poles/dateline and while preserving meaningful strata. That’s an inference from the name alone, not from the repo.

If you paste the repo tree and key files, I can give you an actual review instead of a checklist.
