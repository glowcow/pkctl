# PyKubeCtl tool

## Getting started
### Installation

1. Download binary
   ```bash
   wget https://gitlab.com/api/v4/projects/38089511/packages/generic/pkctl/0.2.0/pkctl-0.2.0
   ```
2. Move to /usr/bin
   ```bash
   sudo mv pkctl-0.2.0 /usr/bin/pkctl
   ```
3. Allow to execute
   ```bash
   sudo chmod +x /usr/bin/pkctl
   ```
### Example usage

Show app version:
```bash
pkctl version
```
Listing all pods on all nodes:
```bash
pkctl pods
```
Listing all pods on specific node:
```bash
pkctl node worker1
```