# LARRYD's listings (sprint item 12): prepared, nothing submitted

Every listing is an outward act for the owner. Nothing here has been sent anywhere. The words to use are in
[text.md](text.md). The places were read on 2026-09-30; each row says whether that was verified.

What is listed is LARRYD itself (the command, its MCP tool server, its Claude Code plugin and skill). The agents
built with it (THE HIRE GUIDE, THE BRAND CATALOG) fit none of these places: they run only on LARRYD, air gapped, and
these places list tools and servers that people install and run themselves.

## Before most of them (the owner's)
1. **The license**: Apache-2.0 on this branch (LICENSE at the root, in plugin/, npm/ and cargo/; the `license` field in
   pyproject.toml, the plugin, package.json and Cargo.toml). It takes effect when the branch is merged (the owner's word).
2. **The repository public**: github.com/larrydaemon/larryd is private today. Almost every place reads the public repository.
3. **LARRYD 0.1.0 on PyPI**: `pip install larryd` gives only the 0.0.1 name reservation until then.

## The 20 places
| # | Place | Lists | Needs | Fits LARRYD? | Prepared here | Verified |
|---|---|---|---|---|---|---|
| 1 | Official MCP Registry (registry.modelcontextprotocol.io) | MCP servers (points at the package) | `server.json`, the package on PyPI, `mcp-name` in the PyPI README, a GitHub login | Yes, once 0.1.0 is on PyPI | [mcp-registry/server.json](mcp-registry/server.json) (valid against the registry's 2025-12-11 schema); the README's `mcp-name` line | yes |
| 2 | Anthropic's directory (claude.ai/directory/manage) | Claude Code plugins, connectors | public repo, `plugin/README.md` of 40+ words, a license, a paid claude.ai plan, review | Yes, once public and licensed; it is held for a reviewer because the server is the pip-installed `larryd` command | `plugin/README.md` (97 words); the plugin passes `claude plugin validate --strict` | yes |
| 3 | `claude-plugins-official` | Anthropic's own choice | an Anthropic partner contact | No: no public submissions | - | yes |
| 4 | Our own plugin marketplace (this repository) | our plugin | the repository public | Yes | `.claude-plugin/marketplace.json` (validated) | yes |
| 5 | Smithery (smithery.ai/new) | MCP servers | an HTTPS server, or an MCPB bundle for a local server | Yes with an MCPB bundle | Not prepared: an MCPB bundle is made and checked with `mcpb` (Node), which this Mac does not have | yes |
| 6 | Glama (glama.ai/mcp/servers) | MCP servers | public repo, `glama.json`, a Dockerfile whose image starts the server | Yes | [docker/Dockerfile](docker/Dockerfile) (built and proven here: the image answers `initialize` and lists the seven tools with no network); [glama/glama.json](glama/glama.json) (needs the owner's GitHub user name) | partly |
| 7 | mcp.so (mcp.so/submit) | servers, clients, agents | the repository URL | Yes, once public | text.md | yes |
| 8 | PulseMCP | MCP servers | fills itself from #1 (its form is paused) | Yes, through #1 | - | yes |
| 9 | MCP Market (mcpmarket.com/submit) | MCP servers, Agent Skills | the repository URL (free queue, 4-6 weeks) | Yes, once public | text.md | yes |
| 10 | GitHub's MCP Registry (github.com/mcp; VS Code's `@mcp` search) | MCP servers | fills itself from #1 | Yes, through #1 | - | yes |
| 11 | awesome-mcp-servers (punkpeye) | MCP servers people run | a pull request adding one line | Yes, once public | the line in text.md | yes |
| 12 | modelcontextprotocol/servers | reference servers only | - | No: no community list any more; it points to #1 | - | yes |
| 13 | Docker MCP Catalog (github.com/docker/mcp-registry) | containerised MCP servers | a pull request with `server.yaml`, a Dockerfile in the repository, an open license | Yes, once licensed open | [docker/Dockerfile](docker/Dockerfile) (proven) | yes |
| 14 | Cline MCP Marketplace (github.com/cline/mcp-marketplace) | MCP servers | an issue: repository, a 400×400 PNG logo, why, proof Cline installs it | Needs LARRYD's logo (the owner's art) | text.md | yes |
| 15 | Cursor Directory (cursor.directory) | Cursor plugins, MCP servers | its form (not read: the page refused the reader) | Probably | text.md | no |
| 16 | awesome-claude-code (hesreallyhim) | Claude Code tools, plugins, skills | a form filled by a person; the repository 14+ days old with ongoing work | Later (the repository's age) | text.md | yes |
| 17 | Agent Skills sites (agent-skills.md; skillsmp.com; skills.sh) | SKILL.md skills | a GitHub link to the skills folder | Yes: `plugin/skills/larryd/SKILL.md` has name and description | - | partly |
| 18 | Plugin indexes (claudemarketplaces.com, claude-plugins.dev) | Claude Code marketplaces | find public repositories themselves | Yes, once public | - | partly |
| 19 | PyPI · npm · crates.io · Docker Hub | packages, images | an upload each; an image push | Yes: the names are ours on all three registries (0.0.1 reservations); npm and cargo carry a thin launcher (npm/, cargo/, built and proven) | pyproject.toml; npm/; cargo/; docker/Dockerfile | yes |
| 20 | Homebrew (own tap) · conda-forge · Product Hunt | CLI tools; conda packages; launches | an open license and fame (Homebrew core); a recipe from the PyPI source + a license (conda-forge); a maker account (Product Hunt) | Own tap and Product Hunt yes; Homebrew core and conda-forge wait on the license and time | text.md | yes |

Fits today, once the repository is public and 0.1.0 is on PyPI: 1, 2 (with a license), 4, 6, 7, 8, 9, 10, 11, 17, 18, 19
(PyPI, Docker Hub), 20 (Product Hunt, own tap). Waits on the license: 13, conda-forge, Homebrew core. Waits on a logo:
14. Waits on time: 16. Not a place for LARRYD: 3, 12.

## The owner's steps, in order (each one outward; one command or page each)
1. Merge the Apache-2.0 branch (`license-apache`): the license is already in every package.
2. Make the repository public: github.com/larrydaemon/larryd → Settings → Change visibility.
3. Publish 0.1.0 together, one version everywhere: PyPI `cd ~/larryd && python3 -m pip install build twine && python3 -m build && python3 -m twine upload dist/*`,
   npm `cd ~/larryd/npm && npm publish`, crates.io `cd ~/larryd/cargo && cargo publish`.
4. Official MCP Registry: `brew install mcp-publisher && cd ~/larryd/listings/mcp-registry && mcp-publisher login github && mcp-publisher publish`
   (PulseMCP and GitHub's MCP Registry fill themselves from it.)
5. Docker Hub: `cd ~/larryd && docker build -f listings/docker/Dockerfile -t larrydaemon/larryd:0.1.0 . && docker push larrydaemon/larryd:0.1.0`
6. Anthropic's directory: https://claude.ai/directory/manage → Submit new → Plugin bundle → repository larrydaemon/larryd, path `plugin/`.
7. Glama: copy `listings/glama/glama.json` (with the owner's GitHub name) and `listings/docker/Dockerfile` to the repository's root, then https://glama.ai/mcp/servers → Add Server.
8. mcp.so: https://mcp.so/submit (the repository link).
9. MCP Market: https://mcpmarket.com/submit (the repository link).
10. Agent Skills: https://agent-skills.md → Submit (the link to `plugin/skills/larryd`).
11. awesome-mcp-servers: a pull request adding the line in text.md.
12. Product Hunt: https://www.producthunt.com/posts/new (the words in text.md).
13. After the license: the Docker MCP Catalog (a pull request to github.com/docker/mcp-registry via its `task wizard`), and conda-forge (a recipe pull request to conda-forge/staged-recipes).
14. After a logo: the Cline MCP Marketplace issue.
15. After 14 days of the public repository: awesome-claude-code's form, filled by a person.
16. Smithery: after an MCPB bundle is made and checked with `mcpb` (needs Node).
