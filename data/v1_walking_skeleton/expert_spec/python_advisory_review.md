# Python Dependency Advisory Applicability Review

## Scope

- MUST CONSTRAINT: Limit each decision to one Python dependency and one frozen advisory record.
- MUST NOT CONSTRAINT: Claim reachability, exploitability, or project compromise from advisory applicability.

## Procedure

- MUST PROCEDURE: Parse one exact pinned dependency version and its environment marker.
- MUST PROCEDURE: Query the frozen OSV advisory record and affected range by advisory identifier.
- MUST PROCEDURE: Match the advisory package name to the normalized dependency inventory.
- MUST PROCEDURE: Compare the pinned version with supported OSV ecosystem range events.
- MUST CONSTRAINT: Return unresolved when the advisory, version, marker result, or required evidence is unknown.
- MUST CONSTRAINT: Record the frozen snapshot, query contract, result digest, and decision reason code.

## Exceptions and negative rules

- MUST NOT CONSTRAINT: Treat a missing advisory as proof that the dependency is safe.
- MUST NOT CONSTRAINT: Use model memory when the frozen knowledge projection is unavailable.
- SHOULD CONSTRAINT: Preserve unsupported requirement syntax as a parse diagnostic.

## Quarantined construction example

- [UNSUPPORTED] Every dependency warning proves that a vulnerability is exploitable.
