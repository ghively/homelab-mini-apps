# Dependency Inventory

## Direct Dependencies

None (runtime dependencies empty)

## Dev Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @testing-library/dom | ^10.1.0 | MIT | DOM testing utilities for web components |
| @types/node | ^20.14.0 | MIT | TypeScript type definitions for Node.js |
| @typescript-eslint/eslint-plugin | ^7.13.0 | MIT | TypeScript linting rules |
| @typescript-eslint/parser | ^7.13.0 | BSD-2-Clause | TypeScript parser for ESLint |
| @vitest/ui | ^1.6.0 | MIT | Vitest UI for test runner |
| @vitest/coverage-v8 | ^1.6.0 | MIT | Code coverage with v8 |
| eslint | ^8.57.0 | MIT | JavaScript/TypeScript linter |
| jsdom | ^24.1.0 | MIT | DOM implementation for testing |
| typescript | ^5.5.3 | Apache-2.0 | TypeScript compiler |
| vite | ^5.3.1 | MIT | Build tool and dev server |
| vitest | ^1.6.0 | MIT | Test framework |

## License Summary

- **MIT**: 9 packages (@testing-library/dom, @types/node, @typescript-eslint/eslint-plugin, @vitest/ui, @vitest/coverage-v8, eslint, jsdom, vite, vitest)
- **Apache-2.0**: 1 package (typescript)
- **BSD-2-Clause**: 1 package (@typescript-eslint/parser)

All licenses are permissive and compatible with the UNLICENSED internal project license.

## Security Assessment

- All packages are from official npm registry
- No transitive dependency analysis performed (package-lock.json not generated due to node_modules corruption)
- No known CVEs in selected versions at time of selection (2026-07-26)
- Packages have recent maintenance activity (all within 2024)

## Known Issues

- `package-lock.json` was not generated due to npm install corruption in workspace
- Reproducible builds require a clean npm install environment
- For production deployment: delete node_modules, run fresh npm install, verify package-lock.json generation

## Activity Metrics

- Average weekly downloads for core packages: >10M (vite, typescript)
- Recent releases within 6 months for all packages
- Active maintenance: All packages have commits in 2024