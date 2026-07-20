# 🔒 Security Guidelines

## API Key Protection

### ✅ What's Protected

All sensitive API keys are properly secured:

- **`.env`** - Main environment file (gitignored)
- **`deploy/.env.ecs`** - ECS deployment environment (gitignored) 
- **Documentation files** - Now use placeholder values only

### 🛡️ .gitignore Coverage

The following files are protected from git commits:

```gitignore
# Environment variables
.env
.env.local
.env.*.local
deploy/.env.ecs

# Documentation files with API keys (protect from accidental commits)
AI_MODEL_CONFIGURATION.md
BACKEND_SETUP.md
MODEL_SWITCH_SUMMARY.md
QUICK_START_GUIDE.md
```

### 🔑 API Key Formats

- **OpenRouter**: `sk-or-v1-[alphanumeric]`
- **DashScope**: `sk-ws-[alphanumeric]`
- **Supabase**: `eyJ[JWT_token]`

### 📋 Safe Deployment Process

1. **Local Development**: Keep real keys in `.env` (gitignored)
2. **Documentation**: Use placeholder values in all docs
3. **ECS Deployment**: Copy template and replace placeholders manually
4. **Repository**: Never commit real API keys

### ⚠️ What to Never Commit

- Real API keys in any file
- `.env` files with actual credentials  
- Screenshots containing API keys
- Log files with authentication tokens

### 🚀 Deployment Security

For ECS deployment:

1. Use `deploy/.env.ecs.template` as starting point
2. Replace ALL placeholder values with real keys
3. Ensure `.env` on ECS instance is properly configured
4. Verify API keys work before deployment

### 🔍 How to Verify Protection

Check that your API keys aren't exposed:

```bash
# Search for any remaining real keys in tracked files
git ls-files | xargs grep -l "sk-or-v1-[a-zA-Z0-9]" || echo "✓ No OpenRouter keys found"
git ls-files | xargs grep -l "sk-ws-[a-zA-Z0-9]" || echo "✓ No DashScope keys found"

# Verify .env is gitignored
git check-ignore .env && echo "✓ .env is properly ignored"
```

### 🛠️ Emergency Key Rotation

If keys are accidentally committed:

1. **Immediately rotate** all exposed API keys
2. **Remove from git history**: `git filter-branch` or BFG Repo Cleaner
3. **Update** all deployment environments
4. **Notify** team members of the incident

### 📞 Reporting Security Issues

If you discover any security vulnerabilities or exposed credentials:

1. **Do not** create a public issue
2. **Contact** repository maintainers directly
3. **Include** details of the vulnerability
4. **Wait** for confirmation before disclosure

---

**Remember**: Security is everyone's responsibility. When in doubt, err on the side of caution and ask for guidance.