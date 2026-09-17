# JQL Patterns by Division

## Privilege Cloud

```jql
(
  PlannedPI in (<pi-list>) AND status != Archived AND issuetype = Theme
  AND Divisions = "Privilege Cloud"
)
OR
(
  Divisions = "Access & Risk"
  AND "User-Defined Participating Products" in (PCloud-PSM, PCloud-PSMP)
  AND issuetype = Theme AND status != Archived
  AND PlannedPI in (<pi-list>)
)
AND NOT labels in (Bucket, bucket)
```

> Note: Some "Access & Risk" themes participate in Privilege Cloud — the second clause captures them via product filter.

## Access & Risk (standalone, not cross-division)

```jql
PlannedPI in (<pi-list>) AND status != Archived AND issuetype = Theme
AND Divisions = "Access & Risk"
AND NOT labels in (Bucket, bucket)
```

## Generic / Unknown Division

```jql
PlannedPI in (<pi-list>) AND status != Archived AND issuetype = Theme
AND Divisions = "<Division Name>"
AND NOT labels in (Bucket, bucket)
```

If the first query returns 0 results, try without the `Divisions` filter and ask the
user to confirm which project keys belong to the division.

---

## Group field (cf[22720]) — not project keys

**Groups always come from `customfield_22720` (Groups field in Jira), not from `project.key`.**

A single theme can belong to multiple groups; always use the **first** value as the primary group.

### Privilege Cloud — observed groups in `cf[22720]`

| Group name in cf[22720] | Description |
|-------------------------|-------------|
| EPV pCloud | Enterprise Password Vault / Privilege Cloud core |
| pCloud | Privilege Cloud platform / shared services |
| DV | Developer Vault / developer-focused products |

> These group names are case-sensitive. Other groups may appear as the division evolves.
> Always read group names from live Jira data rather than hardcoding them.

---

## Pass C JQL — Epic breakdown quality

To count Epics per Theme (Pass C), use the `cf[11140]` (Parent Link) field:

```jql
issuetype = Epic AND cf[11140] in (<theme-key-list>) AND status != Archived
```

- Chunk `<theme-key-list>` into batches of ≤ 50 theme keys to stay within JQL length limits.
- Paginate until all results are fetched.
- Group results by `customfield_11140.key` to get the Epic count per Theme.

---

## PI list formatting

Replace `<pi-list>` with comma-separated PI names matching Jira values exactly,
e.g. `26-Q1, 26-Q2, 27-Q1, 27-Q2`. Ask the user if unsure of the exact PI labels
used in Jira for their context.
