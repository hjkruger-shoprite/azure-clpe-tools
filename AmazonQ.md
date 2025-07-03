# Amazon Q CLI Autocomplete Setup

## Setting up autocomplete for Amazon Q CLI

To enable autocomplete for Amazon Q CLI commands, you need to add the following to your shell configuration file:

### For Zsh (add to ~/.zshrc):
```bash
eval "$(q completion --shell zsh)"
```

### For Bash (add to ~/.bashrc or ~/.bash_profile):
```bash
eval "$(q completion --shell bash)"
```

After adding the appropriate line to your shell configuration file, restart your terminal or run `source ~/.zshrc` (for Zsh) or `source ~/.bashrc` (for Bash) to apply the changes.

## Verifying Autocomplete

Once configured, you should be able to type `q` followed by a space and then press Tab to see available commands and options.
