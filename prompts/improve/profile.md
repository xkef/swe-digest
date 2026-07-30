# Step: improve / profile

Propose changes to the reading profile, which states what the digest is
interested in. **You write nothing.** This is the highest-trust surface in the
repository, so the output is a proposal only, and only an owner-approved comment
turns it into a pull request.

Two kinds of evidence justify a proposal:

- **Owner feedback.** Feedback issues authored by the owner are binding. A
  `not interesting` kind maps to a profile "Lower interest" entry, and a
  `more like this` maps to an addition. Every owner-authored feedback issue
  reviewed in the window maps to either a concrete proposal or a one-line
  rejection with a reason.
- **Interest drift.** A topic present in the account-signal aggregate for three
  or more consecutive weekly markers and absent from both the watchlist and the
  profile. Carry only the normalized aggregate signal into the proposal, never
  raw follow or starred-repo lists.

State the evidence with numbers and dates, give one measurable expected effect
with a check date, and give the rollback line.
