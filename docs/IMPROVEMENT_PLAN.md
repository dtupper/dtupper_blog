# Generator improvement plan

Agreed sequence from the codebase review. Complete and review each phase before starting the next.

## Phase 1: Safe builds and validation

Implemented. Regression tests cover source preservation, draft filtering, failed
builds, rollback, and retained backups. The sample content builds through the CLI.

- Reject output paths that overlap source, configuration, or protected directories, including symlink aliases.
- Contain generated file paths within output.
- Reject malformed YAML, duplicate keys, and invalid publication metadata with source filenames.
- Build in staging; replace output only after success, with rollback on installation failure.
- Preserve a recoverable backup if rollback itself fails.
- Test realistic failures that could delete source, publish drafts, or replace working output.

## Phase 2: Markdown, dates, and route correctness

Implemented. Literal code and article text are preserved, dates and feeds retain
publication instants, and conflicting routes fail before output is replaced.

- Detect unclosed callout/details directives instead of discarding content.
- Preserve fenced, indented, and inline code during Markdown transformations.
- Remove the redundant Markdown metadata parser; make Notion link cleanup opt-in.
- Normalize date handling and timezones; establish stable dates for dated blog URLs.
- Detect route collisions, reserve generated routes, and reject empty slugs.
- Correct RSS ordering and timezone serialization.
- Escape embed attributes and encode URL parameters.
- Check browser badge behavior with focused JavaScript tests.

## Phase 3: Configuration and publishing polish

- Honor or remove ineffective pagination, date-format, locale, and index-template settings.
- Respect configured section URL patterns and support deployment base paths if needed.
- Only advertise feeds and section indexes that exist.
- Reduce duplicate template overrides.
- Add canonical URLs, social-preview metadata, a sitemap, and a useful 404 page.
- Add an installed-wheel CLI smoke test to CI.

## Test rules

- Test plausible inputs and failures, not impossible API calls or irrelevant extra arguments.
- Each test owns its setup and must not depend on another test's outcome.
- Prefer readable setup and assertions over clever or efficient test code.
- Before adding a test, ask: “If this test didn't exist, could something dangerous slip through?”
- Use existing happy-path coverage where sufficient; add focused regression tests for meaningful risks.
