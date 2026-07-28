#!/usr/bin/env bash
# Git credential helper for the PERSONAL dotfiles repo ONLY.
#
# Why this exists: in a Coder workspace, git's default credential
# (git-credential-coder) is a GitHub App token scoped to the Zampfi org, so it
# cannot push to the personal SahilZ0810/dotfiles repo (403). This helper
# supplies a fine-grained PAT for that one repo instead. It is wired ONLY into
# this repo's local git config (see install.sh's wire_dotfiles_repo_credential),
# so it never affects Zampfi repos.
#
# Reuses the same PAT as the obsidian vault's credential helper
# (config/obsidian-vault-credential.sh) — by user choice, since that token
# already has access to this repo too. The token itself is NEVER committed; it
# lives in a file in the workspace's persistent home:
#   printf '%s' 'github_pat_xxx' > ~/.config/obsidian-vault-token && chmod 600 ~/.config/obsidian-vault-token
#
# git calls credential helpers with an operation arg: get | store | erase.
# We only answer "get"; anything else is a no-op.
[ "$1" = get ] || exit 0

TOKEN_FILE="${OBSIDIAN_VAULT_TOKEN_FILE:-$HOME/.config/obsidian-vault-token}"
[ -r "$TOKEN_FILE" ] || exit 0

echo "username=SahilZ0810"
echo "password=$(tr -d '\r\n' < "$TOKEN_FILE")"
