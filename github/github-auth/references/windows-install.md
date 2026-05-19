# Windows gh CLI Installation Pitfalls

## SSL Revocation Errors

On some Windows machines, `curl` and `winget` hit SSL certificate revocation check failures:

```
curl: (35) schannel: next InitializeSecurityContext failed: CRYPT_E_REVOCATION_OFFLINE
```

**Workaround**: Use `--ssl-no-revoke` flag with curl:

```bash
curl --ssl-no-revoke -L -o gh.zip "https://github.com/cli/cli/releases/download/v2.69.0/gh_2.69.0_windows_amd64.zip"
```

## winget Silent Failures

`winget install --id GitHub.cli --silent` can return exit code 1 while appearing to succeed (progress bar completes, hash verified). The package may not actually be installed. Verify with:

```bash
winget list --name "GitHub CLI"
```

If not found, fall back to manual download + extract.

## Manual Install Path

```bash
# Download (with SSL workaround if needed)
curl --ssl-no-revoke -L -o "$HOME/Downloads/gh.zip" \
  "https://github.com/cli/cli/releases/download/v2.69.0/gh_2.69.0_windows_amd64.zip"

# Extract
mkdir -p "$HOME/AppData/Local/Programs/GitHub CLI"
unzip -o "$HOME/Downloads/gh.zip" -d "$HOME/AppData/Local/Programs/GitHub CLI"

# Add to PATH (git-bash/MSYS)
echo 'export PATH="/c/Users/$USER/AppData/Local/Programs/GitHub CLI/bin:$PATH"' >> ~/.bashrc
```

## PATH Refresh

After install, the current shell won't see `gh` until PATH is reloaded. Either:
- Open a new terminal, or
- `export PATH="..."` in current session, or
- `source ~/.bashrc`
