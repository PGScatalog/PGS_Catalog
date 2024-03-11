## About the reference genome QC script

This script verifies if the variant positions of a scoring file match the given reference genome.

### How it works

A sample of variants is taken from the total in the scoring file and tested for match against the reference genome. The reference genome is found using the Ensembl REST API. Two different services can be used depending on the available information of the variants in the scoring file: variants with rsID or variants with coordinates only.

#### Using rsIDs (matching position)

If a _rsID_ column is present, the Ensembl Variation API is used. A variant is considered matching if the both the positions in the scoring file and in the Ensembl API response are equal.

#### Using coordinates (matching nucleotide)

If only the coordinates (_chr_name_ and _chr_position_) are present, the Ensembl Sequence API is used. For each variant, the scripts fetches the nucleotide present at the variant position in the reference genome. Since there is no certainty about which allele is the reference one, both effect and other (if present) alleles are tested, and the variant is considered matching if one of these alleles is equal to the one returned by the API. This means that if the genome build is **not** correct, a match rate of 50% is expected if both effect and other alleles are specified, or 25% if only the effect allele is specified.

#### Sample size

The sample size varies depending on the API service used. The maximum request size of the Sequence API is 50, whereas the maximum size is 200 for the Variation API. However, it is recommended to set a smaller request size for the Variation API as it sometimes returns an empty response if the request size is too close to the maximum allowed. Each of those sizes can be modified in the script by changing the value of **MAX_SEQUENCE_REQUEST_SIZE** and **MAX_VARIATION_REQUEST_SIZE**.

#### Number of samples

Multiple requests to the Ensembl API can be made to increase the size of the total sample of tested variants (see Usage section). A higher number will increase the precision of the validation but slow down the execution. The samples are made from all the scoring file variants without replacement. No more request is made if all the variants have been sampled.

### Usage

```
qc_ref_genome.py [-h] [--scoring_file SCORING_FILE] [--ref {auto,37,38}] [--n_requests N_REQUESTS] [--flip | --no-flip]
```

* *scoring_file* : the scoring file to validate (unzipped)
* *ref*: allowed values: **auto**, **37**, **38**. If set to auto, the reference genome found in the header of the scoring file will be used.
* *n_requests*: maximum number of requests (or number of samples) sent to the Ensembl API. Default: **1**
* *flip*: default is off. If flip is on, all variants will be tested against the reverse strand if using coordinates without rsID.
