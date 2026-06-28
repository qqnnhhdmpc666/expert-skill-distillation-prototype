# Runtime-visible task

{
  "allowed_tools": [
    "read_repo_snapshot",
    "read_allowed_knowledge",
    "local_text_search"
  ],
  "commit_digest": "git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713",
  "expected_output_schema": "expected_output_schema.json",
  "knowledge_access_contract": {
    "advisory_id": "PYSEC-2018-28",
    "forbidden_sources": [
      "internet"
    ],
    "mode": "allowed_snapshot_only",
    "package": "requests"
  },
  "license": "MIT",
  "public_source": {
    "commit_url": "https://github.com/hindupuravinash/the-gan-zoo/commit/375f2be4a852ead8980c06b2a996893f0cb95713",
    "description": "Minimal immutable public excerpt containing the dependency declaration, real import/use site, and upstream license.",
    "fixture_type": "public_repo_excerpt",
    "non_toy_status": "traceable_public_excerpt",
    "repository": "hindupuravinash/the-gan-zoo",
    "source_url": "https://github.com/hindupuravinash/the-gan-zoo",
    "type": "public_repo_excerpt"
  },
  "repo_snapshot_ref": "github:hindupuravinash/the-gan-zoo@375f2be4a852ead8980c06b2a996893f0cb95713",
  "resource_budget": {
    "llm_calls": 0,
    "max_allowed_knowledge_queries": 1,
    "max_repo_files_read": 3,
    "network": "disabled"
  },
  "schema_version": "repo_security_task.v1",
  "skill_condition": {
    "condition_family": "dependency_use_triage",
    "requirements": [
      "identify dependency declaration",
      "extract resolved version",
      "find import or call-site evidence",
      "consult allowed advisory snapshot",
      "abstain when required evidence is missing"
    ]
  },
  "task_id": "dependency_use_triage_the_gan_zoo_public",
  "task_instruction": "Determine whether requests is declared in this public repository excerpt, used in code, and affected according to the allowed frozen advisory snapshot. Return only the required prediction schema.",
  "task_type": "dependency_use_triage"
}

# Expected output schema

{
  "decision_enum": [
    "dependency_used_and_affected",
    "dependency_present_not_used",
    "dependency_used_not_affected",
    "unresolved"
  ],
  "evidence_fields": [
    "evidence_id",
    "evidence_type",
    "path",
    "line_start",
    "line_end",
    "excerpt",
    "file_digest"
  ],
  "required_fields": [
    "schema_version",
    "task_id",
    "task_type",
    "decision",
    "package",
    "declared_version",
    "advisory_id",
    "evidence",
    "reason_codes"
  ],
  "schema_version": "repo_security_prediction_schema.v1"
}

# Repo snapshot manifest

{
  "commit_digest": "git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713",
  "commit_url": "https://github.com/hindupuravinash/the-gan-zoo/commit/375f2be4a852ead8980c06b2a996893f0cb95713",
  "excerpt_policy": "Exact upstream file contents for only the dependency declaration, runtime use site, and license.",
  "files": [
    {
      "line_count": 21,
      "original_path": "LICENSE",
      "path": "LICENSE",
      "role": "license",
      "sha256": "sha256:5a2f49a84e901f7bd8b4263932eb36eadb887a1b9f5e80c656b8030fe595e257",
      "source_url": "https://github.com/hindupuravinash/the-gan-zoo/blob/375f2be4a852ead8980c06b2a996893f0cb95713/LICENSE",
      "upstream_git_blob": "ab73f9b4fffc6c63c2f79191ec57fb341b1b1ae0"
    },
    {
      "line_count": 25,
      "original_path": "requirements.txt",
      "path": "requirements.txt",
      "role": "dependency_declaration",
      "sha256": "sha256:d1d8962369ac9d2368d5810fb179dde2c3783dfc97e30350d51e3a608dda1011",
      "source_url": "https://github.com/hindupuravinash/the-gan-zoo/blob/375f2be4a852ead8980c06b2a996893f0cb95713/requirements.txt",
      "upstream_git_blob": "8cf85d08165848ec70733319b14069eb53f1313b"
    },
    {
      "line_count": 78,
      "original_path": "update.py",
      "path": "update.py",
      "role": "runtime_use_site",
      "sha256": "sha256:3c8f7bc806af47360aa8dab1891b4947921eec666b3e828764e571aab3429b66",
      "source_url": "https://github.com/hindupuravinash/the-gan-zoo/blob/375f2be4a852ead8980c06b2a996893f0cb95713/update.py",
      "upstream_git_blob": "cfcbfcd48f5c419bb4bf0649dfa9b308f4354d97"
    }
  ],
  "fixture_type": "public_repo_excerpt",
  "language": "python",
  "license": "MIT",
  "repo_snapshot_ref": "github:hindupuravinash/the-gan-zoo@375f2be4a852ead8980c06b2a996893f0cb95713",
  "repository": "hindupuravinash/the-gan-zoo",
  "schema_version": "repo_snapshot_manifest.v1",
  "snapshot_content_digest": "sha256:4fa32e652b51130309c78b9d4f52a3020bd5930b289a015e5dc6626c90286ccb",
  "snapshot_id": "the-gan-zoo@375f2be4a852ead8980c06b2a996893f0cb95713:dependency-use-excerpt",
  "source_tree_digest": "git-sha1:1d14483f75314b681832854d7d766db179d6b788",
  "source_url": "https://github.com/hindupuravinash/the-gan-zoo"
}

# Allowed frozen knowledge snapshot

{
  "knowledge_sources": [
    {
      "affected_ranges": [
        {
          "fixed": "2.20.0",
          "introduced": "0"
        }
      ],
      "aliases": [
        "CVE-2018-18074",
        "GHSA-x84v-xcm2-53pg"
      ],
      "allowed_claim": "The frozen OSV advisory marks requests versions before 2.20.0 as affected.",
      "database_specific_source": "https://github.com/pypa/advisory-database/blob/main/vulns/requests/PYSEC-2018-28.yaml",
      "ecosystem": "PyPI",
      "not_allowed_claims": [
        "exploitability in the repository deployment",
        "runtime reachability beyond the recorded import/use site",
        "credential exposure in any real deployment",
        "general vulnerability discovery"
      ],
      "package": "requests",
      "source_id": "PYSEC-2018-28",
      "source_kind": "security_advisory_snapshot",
      "source_modified": "2023-11-08T04:00:04.815794Z",
      "source_url": "https://api.osv.dev/v1/vulns/PYSEC-2018-28"
    }
  ],
  "retrieved_at": "2026-06-26T00:00:00+08:00",
  "schema_version": "allowed_knowledge_snapshot.v1",
  "snapshot_policy": "frozen_public_advisory_excerpt"
}

# repo_snapshot/requirements.txt with 1-based line numbers

001: astroid==2.0.4
002: beautifulsoup4==4.6.3
003: bs4==0.0.1
004: certifi==2018.8.24
005: chardet==3.0.4
006: cycler==0.10.0
007: idna==2.7
008: isort==4.3.4
009: Jinja2==2.10
010: kiwisolver==1.0.1
011: lazy-object-proxy==1.3.1
012: MarkupSafe==1.0
013: matplotlib==2.2.3
014: mccabe==0.6.1
015: numpy==1.15.1
016: Pillow==5.2.0
017: pylint==2.1.1
018: pyparsing==2.2.0
019: python-dateutil==2.7.3
020: pytz==2018.5
021: requests==2.19.1
022: six==1.11.0
023: typed-ast==1.1.0
024: urllib3==1.23
025: wrapt==1.10.11

# repo_snapshot/update.py with 1-based line numbers

001: # -*- coding: utf-8 -*-
002: """ Update Readme.md and cumulative_gans.jpg """
003: from __future__ import print_function
004: from __future__ import division
005:
006: import numpy as np
007: import matplotlib.pyplot as plt
008: from bs4 import BeautifulSoup
009: import requests
010: import csv
011:
012:
013: def load_data():
014:     """ Load GANs data from the gans.csv file """
015:
016:     with open('gans.tsv') as fid:
017:         reader = csv.DictReader(fid, delimiter='\t')
018:         gans = [row for row in reader]
019:     return gans
020:
021:
022: def update_readme(gans):
023:     """ Update the Readme.md text file from a Jinja2 template """
024:     import jinja2 as j2
025:
026:     gans.sort(key=lambda v: v['Abbr.'].upper())
027:     j2_env = j2.Environment(loader=j2.FileSystemLoader('.'),
028:                             trim_blocks=True, lstrip_blocks=True)
029:
030:     with open('README.md', 'w') as fid:
031:         print(j2_env.get_template('README.j2.md').render(gans=gans), file=fid)
032:
033:
034: def update_figure(gans):
035:     """ Update the figure cumulative_gans.jpg """
036:     data = np.array([int(gan['Year']) + int(gan['Month']) / 12
037:                      for gan in gans])
038:     x_range = int(np.ceil(np.max(data) - np.min(data)) * 12) + 1
039:     y_range = int(np.ceil(data.size / 10)) * 10 + 1
040:
041:     with plt.style.context("seaborn"):
042:         plt.hist(data, x_range, cumulative="True")
043:         plt.xticks(range(2014, 2019))
044:         plt.yticks(np.arange(0, y_range, 15))
045:         plt.title("Cumulative number of named GAN papers by month")
046:         plt.xlabel("Year")
047:         plt.ylabel("Total number of papers")
048:         plt.savefig('cumulative_gans.jpg')
049:
050: def update_github_stats(gans):
051:     """ Update Github stats """
052:     num_rows = len(gans)
053:     print('Fetching Github stats...')
054:     for i, gan in enumerate(gans):
055:         url = gan['Official_Code']
056:         if url != "-" and url != "":
057:             print(str(i) + '/' + str(num_rows))
058:             result = requests.get(url)
059:             c = result.text
060:             soup = BeautifulSoup(c, "html.parser")
061:             samples = soup.select("a.social-count")
062:             gan['Watches'] = samples[0].get_text().strip().replace(",", "")
063:             gan['Stars'] = samples[1].get_text().strip().replace(",", "")
064:             gan['Forks'] = samples[2].get_text().strip().replace(",", "")
065:
066:     print(str(i) + '/' + str(num_rows))
067:     print('Complete.')
068:
069:     with open('gans.tsv', 'w') as outfile:
070:         fp = csv.DictWriter(outfile, gans[0].keys(), delimiter='\t')
071:         fp.writeheader()
072:         fp.writerows(gans)
073:
074: if __name__ == '__main__':
075:     GANS = load_data()
076:     update_readme(GANS)
077:     update_figure(GANS)
078:     update_github_stats(GANS)

# Document-to-Agent Bundle guidance

# Extracted Dependency-Use Triage Skill

1. Inspect dependency declarations first. Accept direct pinned declarations from `requirements.txt`, lock files, or equivalent project metadata.
2. Resolve the declared package version before deciding whether an advisory applies.
3. Inspect import or runtime use sites. A declared dependency with no import/use evidence must not be reported as used and affected.
4. Compare the resolved version against the advisory affected range. A fixed or outside-range version must be reported as used but not affected.
5. A valid `dependency_used_and_affected` decision requires declaration evidence, resolved version evidence, import/use evidence, advisory affected-range evidence, and decision evidence.
6. If required evidence is missing, choose `dependency_present_not_used` or `unresolved`; do not force an affected decision.
7. Produce a schema-valid decision with evidence references containing file path, evidence type, and line/span when available.

## Scope
- Local repo-level dependency-use triage only.


# Knowledge manifest

{
  "evidence_refs": [
    {
      "evidence_type": "expert_material_fact",
      "source_ref": "input_material.md#Factual and Evidence Knowledge"
    },
    {
      "evidence_type": "advisory_snapshot",
      "source_ref": "public_heldout_v0/the-gan-zoo/allowed_knowledge.json"
    },
    {
      "evidence_type": "import_use_site",
      "source_ref": "public_heldout_v0/the-gan-zoo/repo_snapshot/update.py"
    }
  ],
  "facts": [
    "Advisory source id: `PYSEC-2018-28`.",
    "Package: `requests`.",
    "Affected version range for this bounded case: introduced `0`, fixed `2.20.0`.",
    "Runtime-visible repository evidence includes dependency declaration files, Python source files, and allowed advisory snapshots.",
    "Evaluator-only gold answers and verifier implementation details are not runtime-visible knowledge."
  ],
  "knowledge_boundary": "Concrete advisory facts and repository evidence remain outside the stable Skill procedure.",
  "schema_version": "document_to_agent_knowledge_manifest.v0",
  "source": "input_material.md"
}

# ReleaseBundle manifest

{
  "agent_artifact_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-agent-skill",
      "artifact_schema_version": "agent_skill_artifact.v1",
      "digest": "sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d",
      "media_type": "text/markdown",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 758
    }
  ],
  "compatible_agent_profiles": [
    "repo-level-dependency-use-triage-v1"
  ],
  "dependency_manifest_ref": {
    "artifact_id": "repo-level-dependency-use-triage-dependency-manifest",
    "artifact_schema_version": "dependency_manifest.v1",
    "digest": "sha256:ed31ddcef86a4a8d9892362d3d5db6e1652602475d39a63c54f63304ac30d57b",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 4956
  },
  "domain_adapter_ref": {
    "artifact_id": "repo-level-dependency-use-triage-domain-adapter",
    "artifact_schema_version": "domain_adapter.v1",
    "digest": "sha256:d0c3d40d98169d41b36e2e4c7e0255cca3cfe351c90c71b73ee7faac47197d51",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 83
  },
  "domain_primitive_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-evidence-binding-plan",
      "artifact_schema_version": "evidence_binding_plan.v1",
      "digest": "sha256:06d9929fe37787e95068062570d201ae55a8c68fd545b309813fd2b220af912e",
      "media_type": "application/json",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 1561
    }
  ],
  "knowledge_access_binding_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-access-binding",
      "artifact_schema_version": "knowledge_access_binding.v1",
      "digest": "sha256:271d003ce27197c25bde1040d6ef19f6ae70a57fa12d67de1cb98ecaf8787894",
      "media_type": "application/json",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 1029
    }
  ],
  "knowledge_ir_ref": {
    "artifact_id": "repo-level-dependency-use-triage-knowledge-ir",
    "artifact_schema_version": "knowledge_ir.v1",
    "digest": "sha256:601ec7a1d6849c36b85db8a7792b3366977a35ca117fb4026125739a6d2dd786",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 5690
  },
  "knowledge_projection_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-knowledge-projection",
      "artifact_schema_version": "knowledge_projection.v1",
      "digest": "sha256:0792d9afd5a78642fc8ce44fa5ae5baa5c21271d83c4f445b7ad39cf05bd0b35",
      "media_type": "application/json",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 2486
    }
  ],
  "permission_request_ref": {
    "artifact_id": "repo-level-dependency-use-triage-permission-request",
    "artifact_schema_version": "permission_request.v1",
    "digest": "sha256:0479e6db0ecb2db688ab454689cc90099c7d0b9515a7110f1e1c7f409014d644",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 100
  },
  "promotion_verifier_binding_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-promotion-verifier",
      "artifact_schema_version": "verifier_binding.v1",
      "digest": "sha256:cf08506229937f07f23607fbd5f7738e69ec7fa8f64eb17212b39373ab9c4578",
      "media_type": "application/json",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 84
    }
  ],
  "provenance_manifest_ref": {
    "artifact_id": "repo-level-dependency-use-triage-provenance",
    "artifact_schema_version": "bundle_provenance.v1",
    "digest": "sha256:087662b389be1885060bc1f1ee4b575425b895c159a2e1d5c40a04a7dc701e6d",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 2453
  },
  "provider_adapter_refs": [],
  "provider_policy_ref": {
    "artifact_id": "repo-level-dependency-use-triage-provider-policy",
    "artifact_schema_version": "provider_policy.v1",
    "digest": "sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 156
  },
  "runtime_compiler_ref": {
    "artifact_id": "repo-level-dependency-use-triage-runtime-compiler",
    "artifact_schema_version": "runtime_compiler.v1",
    "digest": "sha256:0cbc3f8a12697af42e602f0aae885f3435ba21249764a1340c75d108aa3431b3",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 100
  },
  "runtime_verifier_binding_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-runtime-verifier",
      "artifact_schema_version": "verifier_binding.v1",
      "digest": "sha256:bcb3893b732379d5c33ec1a4accbbe4e4dbc2f42d69687ac0c9979931ffb86e3",
      "media_type": "application/json",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 97
    }
  ],
  "schema_bundle_ref": {
    "artifact_id": "repo-level-dependency-use-triage-schema-bundle",
    "artifact_schema_version": "schema_bundle.v1",
    "digest": "sha256:afb4d96e462da69bf7c119d47c8ceb85553504d3bd8b7cde4241d32e21bdf6eb",
    "media_type": "application/json",
    "schema_version": "artifact_ref.v1",
    "size_bytes": 126
  },
  "schema_version": "release_bundle.v1",
  "skill_family": "repo-dependency-use-triage",
  "skill_ir_refs": [
    {
      "artifact_id": "repo-level-dependency-use-triage-skill-ir",
      "artifact_schema_version": "skill_ir.v1",
      "digest": "sha256:9a816589d50e3358aa1c3c1405e00e8b9f6acf9e36de78d9ba2534b130a98107",
      "media_type": "application/json",
      "schema_version": "artifact_ref.v1",
      "size_bytes": 2021
    }
  ],
  "variant": "document_to_agent_e2e_v0"
}

# Bundle runtime output contract

- For dependency declaration evidence, use evidence_type `dependency_declaration`.
- For resolved package version evidence, add a separate evidence item with evidence_type `resolved_version`.
- For imports or call sites, use evidence_type `import_use_site`, not `import_statement` or `call_site`.
- For the advisory range in allowed_knowledge.json, use evidence_type `advisory_affected_range`, path `allowed_knowledge.json`, source_id `PYSEC-2018-28`, and excerpt containing introduced/fixed range.
- The advisory evidence object must include this exact extra field: `"source_id": "PYSEC-2018-28"`; otherwise the local verifier cannot resolve the allowed knowledge source.
- Add one evidence item with evidence_type `decision_evidence`, path `derived`, and excerpt explaining the final decision from the gathered evidence.
- If version 2.19.1 is compared against fixed 2.20.0 and import/use evidence exists, use reason_codes `VERSION_IN_AFFECTED_RANGE` and `IMPORT_USE_SITE_FOUND`.
- Advisory evidence skeleton: {"evidence_id":"...","evidence_type":"advisory_affected_range","path":"allowed_knowledge.json","source_id":"PYSEC-2018-28","line_start":null,"line_end":null,"file_digest":null,"excerpt":"{\"introduced\": \"0\", \"fixed\": \"2.20.0\"}"}.
- Decision evidence skeleton: {"evidence_id":"...","evidence_type":"decision_evidence","path":"derived","line_start":null,"line_end":null,"file_digest":null,"excerpt":"decision=dependency_used_and_affected; required=dependency_declaration,resolved_version,import_use_site,advisory_affected_range,decision_evidence"}.


Return only one JSON object. Do not include markdown. Evidence paths must be exactly requirements.txt, update.py, allowed_knowledge.json, or derived. Include line_start, line_end, excerpt, and file_digest when evidence is a repo file. Do not request or infer evaluator-only material.