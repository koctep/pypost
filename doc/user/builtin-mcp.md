# Built-in MCP Collections

Use **Built-in** as the collection source in **MCP Servers…** to expose a curated
collection shipped with PyPost. These are inbound servers: an agent calls PyPost's
saved tools. For outbound connections, see the [MCP Client Guide](mcp-client.md).

## Create a Built-in server

1. Open **MCP Servers…** and choose **Add…**.
2. Choose **Built-in** as the collection source and select a shipped collection.
3. Choose a workspace environment, or use **Create editable copy of paired environment**
   when the selected collection provides a template.
4. Choose the server name, host, and a unique port, then **Save**.
5. Select the saved server and choose **Start**. Inspect its tools in **MCP Servers…**.

The **read-only** marker means the shipped collection cannot be edited in your workspace.
It does not prevent starting the server. Use a workspace copy when you need to change
requests. Prefer the default localhost host, `127.0.0.1`.

## Copy the paired environment

**Create editable copy of paired environment** saves a private workspace environment and
selects it for this server. It keeps non-secret defaults and the template's hidden-key
and overridable-variable settings; hidden values start empty. Open the environment manager
to fill in credentials or change defaults before invoking tools that need them.

The copied environment is editable and keeps its own identity even after a rename. It is
independent of the shipped template and does not automatically receive template updates.
You can also choose an existing workspace environment instead of making a copy.

Creating the copy saves the environment immediately. **Cancel** closes the server editor
without saving a new server or changing an existing server; the environment copy remains
in your workspace. **Save** associates the selected environment with that server.

## Receive shipped collection updates

A server whose source remains **Built-in** resolves the installed shipped collection on
its next start. After upgrading PyPost, stop and start the server to expose the updated
requests and tools. A running server keeps the tools loaded when it started.

Your selected workspace environment stays associated with the server. Updating a shipped
collection does not replace your environment or fill in its credentials.

## Copy a collection for editing

In a Built-in server editor, choose **Copy for editing**. PyPost saves a separate editable
workspace collection, switches the source to **Workspace**, and selects that copy while
keeping the selected environment. Requests keep their contents and behavior; the copy has
independent identities and a unique name such as `Collection (copy)`.

The visible update note explains that the copy **no longer receives shipped updates**.
Edit its requests in the workspace collection tree. Repeated copies get separate names and
identities, so edits to one do not affect another or the shipped original.

**Save** changes this server to use the selected workspace copy. **Cancel** leaves the
existing server on its previous Built-in source, while the already saved collection copy
remains in the workspace. Other servers are unaffected.

## Relationship to the examples library

Built-in collections are a curated view of the shipped examples library. **Library
Manager** provides the broader library workflow, including **whole-library copying**;
**Copy for editing** in the MCP server editor copies only the selected collection.

Existing servers configured through the **examples library** are **not automatically
migrated** to the Built-in source. Existing workspace copies are also **not migrated**,
converted back to Built-in, or overwritten by shipped updates. Keep their existing
configuration, or explicitly edit a server's source when you want to change it.

## Troubleshooting

- If a paired environment action is unavailable, select a Built-in collection that has a
  paired template, or choose/create an environment manually.
- If copying is temporarily unavailable while workspace data loads or imports, wait for
  that work to finish and retry. A failed copy keeps the current source and selection;
  check the displayed error and workspace storage access.
- If a Built-in collection disappears after installation or upgrade, verify the installed
  bundle and choose an available entry. A detached workspace copy uses its persisted
  collection and can continue without that shipped bundle.
- If expected new tools are absent, check that the server still uses **Built-in**, then
  stop and start it. Workspace copies intentionally keep their own requests.

See [MCP Tools for AI Agents](mcp-tools.md) for tool configuration and agent connections.
