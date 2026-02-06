# Contributing to Enterprise Platform RHEL-K8s

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, versions, etc.)

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Guidelines

### Ansible Playbooks

- Follow Ansible best practices
- Use YAML linting (`ansible-lint`)
- Test on both RHEL 8 and RHEL 9
- Document variables in comments

### Docker Images

- Use multi-stage builds
- Minimize image size
- Run as non-root user
- Include health checks
- Scan for vulnerabilities

### Kubernetes Manifests

- Validate with `kubectl apply --dry-run`
- Follow naming conventions
- Include resource limits
- Add labels and annotations

### Documentation

- Update README for significant changes
- Keep documentation in sync with code
- Use clear, concise language
- Include examples

## Testing

- Test Ansible playbooks with `--check` mode
- Build Docker images locally
- Validate Kubernetes manifests
- Run CI/CD pipeline before submitting PR

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
