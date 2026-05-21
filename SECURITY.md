# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in Shopsphere, please email us at **security@shopsphere.com** instead of using the issue tracker.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

We appreciate your responsible disclosure and will work with you to fix the issue promptly.

## Security Best Practices

### For Users
- Change default admin password
- Use strong passwords (min 12 characters)
- Keep your account information private
- Don't share session tokens

### For Developers
- Keep dependencies updated
- Use environment variables for secrets
- Enable HTTPS in production
- Implement rate limiting
- Regular security audits
- Validate all inputs
- Use parameterized queries
- Keep logs of security events

## Deployment Security Checklist

- [ ] Change all default passwords
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure HTTPS/SSL
- [ ] Set up database backups
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted domains
- [ ] Set secure cookie flags
- [ ] Regular dependency updates
- [ ] Security headers configured
- [ ] Logging and monitoring enabled

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| 2.0.x   | ✅        | Current stable |
| 1.0.x   | ⚠️        | Security fixes only |
| < 1.0   | ❌        | Not supported |

## Known Vulnerabilities

None currently known. Please report any findings responsibly.
