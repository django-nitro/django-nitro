# Changelog

All notable changes to Django Nitro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Django Nitro
- `NitroComponent` base class for reactive components
- `ModelNitroComponent` for Django ORM integration
- `CrudNitroComponent` with pre-built CRUD operations
- AlpineJS integration via `nitro.js`
- Django Ninja API endpoint for component dispatch
- Pydantic-based state validation with full type safety
- Built-in integrity verification for secure fields
- Automatic state synchronization between server and client
- Support for component actions with parameters
- Messages system for success/error notifications
- Field-level error handling
- Example project with Property and Tenant management

### Security
- HMAC-based integrity tokens to prevent client-side tampering
- Automatic protection for `id` fields and foreign keys
- CSRF token integration with Django

## [0.1.0] - 2024-XX-XX

### Added
- Initial public release

[Unreleased]: https://github.com/django-nitro/django-nitro/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/django-nitro/django-nitro/releases/tag/v0.1.0
