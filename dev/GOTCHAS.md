# Gotchas & Unexpected Findings

## 1. Model Cost Map is Remote by Default

**What:** `litellm.model_cost` loads from a **remote URL by default**, not the local `model_prices_and_context_window.json` file.

**Impact:** Local changes to the JSON file won't be reflected until you:
1. Copy to `litellm/model_prices_and_context_window_backup.json`, OR
2. Set `LITELLM_LOCAL_MODEL_COST_MAP=True`, OR  
3. Use `litellm.register_model()` to manually register models

**Solution:**
```yaml
# In proxy_server_config.yaml
general_settings:
  local_model_cost_map: True  # ← Forces local JSON loading
```

**Reference:** `litellm/litellm_core_utils/get_model_cost_map.py:16-28`

---

## 2. UI Caching Requires Multiple Restarts

**What:** When developing the UI, changes require restarting BOTH the proxy AND the UI dev server.

**Why:**
- Proxy serves the built UI from `.next/` or `out/`
- Dev server caches TypeScript compilations
- Browser caches JavaScript bundles

**Solution:**
1. Make UI changes
2. Rebuild: `cd ui/litellm-dashboard && npm run build` OR `./build_ui.sh`
3. Clear `.next` cache if needed: `rm -rf .next`
4. Restart proxy: `Ctrl+C` then `poetry run litellm --config ...`
5. Restart UI dev server (if using npm run dev)
6. Hard refresh browser: `Cmd+Shift+R`

---

## 3. Provider Enum Must Match Exactly

**What:** The UI's `Providers` enum must have entries in ALL three places:

1. **Enum definition** (`provider_info_helpers.tsx`):
   ```typescript
   export enum Providers {
     Hosted_Lexiq_Nova = "Lexiq Nova",
   }
   ```

2. **Provider map** (lowercase):
   ```typescript
   export const provider_map: Record<string, string> = {
     Hosted_Lexiq_Nova: "remodlai",
   }
   ```

3. **Credential fields** (`provider_specific_fields.tsx`):
   ```typescript
   const PROVIDER_CREDENTIAL_FIELDS: Record<Providers, ProviderCredentialField[]> = {
     [Providers.Hosted_Lexiq_Nova]: [...]
   }
   ```

**Missing any one** causes TypeScript build errors.

---

## 4. Enable Tag Filtering is Required

**What:** Tag-based routing silently fails if `enable_tag_filtering: True` is not set.

**Symptom:** Requests go to random/first deployment instead of tag-matched ones.

**Solution:**
```yaml
router_settings:
  enable_tag_filtering: True  # ← Required for tag routing to work
```

**Reference:** `litellm/router_strategy/tag_based_routing.py:51-52`

---

## 5. Callbacks Must Be Importable Paths

**What:** Callback paths in `litellm_settings.callbacks` must be full Python import paths.

**Wrong:**
```yaml
callbacks: nova_task_routing.nova_task_router  # ❌ Won't find
```

**Correct:**
```yaml
callbacks: litellm.proxy.hooks.nova_task_routing.nova_task_router  # ✅
```

**Reference:** Docs at https://docs.litellm.ai/docs/proxy/call_hooks

---

## 6. Task Parameter Must Be in Request Body

**What:** Unlike `metadata.tags` which can be in body OR header (`x-litellm-tags`), the `task` parameter for Nova must be in the request body.

**Why:** The hook extracts from `data` dict, which is the parsed request body.

**Workaround:** If you need header-based task routing, extend the hook to check headers too.

---

## 7. Model Name Prefix Matching is Substring-Based

**What:** The hook checks `if "nova-embeddings" in model`, which means it activates for:
- ✅ `nova-embeddings-v1`
- ✅ `remodlai/nova-embeddings-v1`  
- ✅ `nova-embeddings-retrieval`
- ❌ `my-nova-model` (false positive)

**Impact:** Use "nova-embeddings" in model names for consistency.

---

## 8. Tags Are Additive, Not Exclusive

**What:** If request has `tags: ["custom"]` and hook adds `["retrieval"]`, final tags are `["custom", "retrieval"]`.

**Routing:** Deployment matches if ANY tag overlaps (OR logic, not AND).

**Implication:** Be careful with custom tags on Nova requests.

**Reference:** `litellm/router_strategy/tag_based_routing.py:29` - `any(tag in deployment_tags for tag in request_tags)`

---

## 9. Default Tag Behavior

**What:** Deployments with `tags: ["default"]` catch ALL untagged requests, including Nova requests without a task.

**Solution:** Either:
- Require `task` parameter (add validation in hook)
- Set one Nova adapter as default
- Use specific model names (`nova-embeddings-retrieval`) instead of generic (`nova-embeddings-v1`)

---

## 10. Hyphen vs Underscore in Directory Names

**What:** Python can't import modules with hyphens in directory names.

**Wrong:** `litellm/llms/lexiq-nova/` ❌  
**Correct:** `litellm/llms/remodlai/` ✅

**Impact:** Had to rename `lexiq-nova` → `remodlai` before imports worked.
