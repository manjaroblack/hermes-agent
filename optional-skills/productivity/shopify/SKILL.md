---
name: shopify
description: Query Shopify Admin/Storefront GraphQL APIs via curl.
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [SHOPIFY_ACCESS_TOKEN, SHOPIFY_STORE_DOMAIN]
  commands: [curl, jq]
required_environment_variables:
  - name: SHOPIFY_ACCESS_TOKEN
    prompt: Shopify Admin API access token (starts with shpat_)
    help: "Shopify admin → Settings → Apps and sales channels → Develop apps → Create an app → API credentials. Token shown ONCE on install."
  - name: SHOPIFY_STORE_DOMAIN
    prompt: Your shop subdomain without protocol (e.g. my-store.myshopify.com)
    help: "The permanent myshopify.com domain, not your custom domain."
  - name: SHOPIFY_API_VERSION
    prompt: Shopify API version (default 2026-01)
    help: "Stable quarterly version. Override if you need an older one."
metadata:
  hermes:
    tags: [Shopify, E-commerce, Commerce, API, GraphQL]
    related_skills: [airtable, xurl]
    homepage: https://shopify.dev/docs/api/admin-graphql
---

# Shopify Admin and Storefront GraphQL

role: Shopify GraphQL read/write API operator
do: configure token/domain/version; query admin/storefront; paginate; inspect GraphQL/user errors/cost; manage products/orders/customers/inventory/metafields; run bulk/webhooks; confirm destructive mutations
inputs: shop domain; API token/version; GraphQL query/variables; GID; resource/mutation intent; webhook URL/app secret
outputs: parseable GraphQL data; resource mutations; cost/pagination status; JSONL export; webhook registration/HMAC result
¬: use legacy REST for new integrations; expose tokens; strip GID prefix; treat HTTP 200 as success; ignore `errors`/`userErrors`; exceed cost bucket; mutate production without confirmation; use access token for webhook HMAC

Use `curl` against Shopify GraphQL. Admin GraphQL handles store operations;
Storefront GraphQL handles read-only customer-facing products, collections, and
cart. REST Admin API is legacy since 2024-04 and receives security fixes only.

## When to Use

- list/search/create/update products/variants
- inspect orders/customers and shipping data
- read/adjust/set inventory by item/location
- read/set metafields/metaobjects
- Storefront read-only queries, bulk exports, webhooks

## Prerequisites

1. Shopify admin → **Settings → Apps and sales channels → Develop apps → Create an app**.
2. **Configure Admin API scopes**; select only needed scopes; save.
3. **Install app**; access token appears once, starts `shpat_`; copy immediately.
4. Store in `${HERMES_HOME:-~/.hermes}/.env`:

   ```
   SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
   SHOPIFY_STORE_DOMAIN=my-store.myshopify.com
   SHOPIFY_API_VERSION=2026-01
   ```

As of January 1, 2026, new admin-created legacy custom apps are gone. For a
shop without an existing custom app after that date, use Dev Dashboard:
https://shopify.dev/docs/apps/build/dev-dashboard. Existing admin apps remain.

Scopes by task:

- products/collections: `read_products`, `write_products`
- inventory: `read_inventory`, `write_inventory`, `read_locations`
- orders: `read_orders`, `write_orders` (30 most recent without `read_all_orders`)
- customers: `read_customers`, `write_customers`
- draft orders: `read_draft_orders`, `write_draft_orders`
- fulfillments: `read_fulfillments`, `write_fulfillments`
- metafields/metaobjects: matching resource scopes

## Procedure

### 1. Apply API basics

- Admin endpoint: `https://$SHOPIFY_STORE_DOMAIN/admin/api/$SHOPIFY_API_VERSION/graphql.json`
- Admin auth: `X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN`, not `Authorization`
- always `POST`, `Content-Type: application/json`, body `{"query": "...", "variables": {...}}`
- HTTP 200 may still contain top-level `errors` or mutation `userErrors`; check both
- IDs are GIDs, e.g. `gid://shopify/Product/10079467700516`; pass verbatim
- rate data is `extensions.cost`: `requestedQueryCost`, `actualQueryCost`, `throttleStatus.{currentlyAvailable, maximumAvailable, restoreRate}`; back off below next query cost; standard 100/50s, Plus 1000/100

Reusable shell function:

```bash
shop_gql() {
  local query="$1"
  local variables="${2:-{}}"
  curl -sS -X POST \
    "https://${SHOPIFY_STORE_DOMAIN}/admin/api/${SHOPIFY_API_VERSION:-2026-01}/graphql.json" \
    -H "Content-Type: application/json" \
    -H "X-Shopify-Access-Token: ${SHOPIFY_ACCESS_TOKEN}" \
    --data "$(jq -nc --arg q "$query" --argjson v "$variables" '{query: $q, variables: $v}')"
}
```

Pipe through `jq` for readability; `-sS` preserves errors and hides progress.

### 2. Discover shop/version

```bash
shop_gql '{ shop { name myshopifyDomain primaryDomain { url } currencyCode plan { displayName } } }' | jq
```

```bash
shop_gql '{ publicApiVersions { handle supported } }' | jq '.data.publicApiVersions[] | select(.supported)'
```

### 3. Products

Search first 20:

```bash
shop_gql '
query($q: String!) {
  products(first: 20, query: $q) {
    edges { node { id title handle status totalInventory variants(first: 5) { edges { node { id sku price inventoryQuantity } } } } }
    pageInfo { hasNextPage endCursor }
  }
}' '{"q":"hoodie status:active"}' | jq
```

Query grammar supports `title:`, `sku:`, `vendor:`, `product_type:`,
`status:active`, `tag:`, `created_at:>2025-01-01`:
https://shopify.dev/docs/api/usage/search-syntax.

Cursor pagination:

```bash
shop_gql '
query($cursor: String) {
  products(first: 100, after: $cursor) {
    edges { cursor node { id handle } }
    pageInfo { hasNextPage endCursor }
  }
}' '{"cursor":null}'
# subsequent calls: pass the previous endCursor
```

Product variants/metafields:

```bash
shop_gql '
query($id: ID!) {
  product(id: $id) {
    id title handle descriptionHtml tags status
    variants(first: 20) { edges { node { id sku price compareAtPrice inventoryQuantity selectedOptions { name value } } } }
    metafields(first: 20) { edges { node { namespace key type value } } }
  }
}' '{"id":"gid://shopify/Product/10079467700516"}' | jq
```

Create product:

```bash
shop_gql '
mutation($input: ProductCreateInput!) {
  productCreate(product: $input) {
    product { id handle }
    userErrors { field message }
  }
}' '{"input":{"title":"Test Hoodie","status":"DRAFT","vendor":"Hermes","productType":"Apparel","tags":["test"]}}'
```

Recent versions use variant mutations:

```bash
# Add variants after creating the product
shop_gql '
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkCreate(productId: $productId, variants: $variants) {
    productVariants { id sku price }
    userErrors { field message }
  }
}' '{"productId":"gid://shopify/Product/...","variants":[{"optionValues":[{"optionName":"Size","name":"M"}],"price":"49.00","inventoryItem":{"sku":"HD-M","tracked":true}}]}'
```

```bash
shop_gql '
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id sku price }
    userErrors { field message }
  }
}' '{"productId":"gid://shopify/Product/...","variants":[{"id":"gid://shopify/ProductVariant/...","price":"55.00"}]}'
```

### 4. Orders

Recent orders (last 30 without `read_all_orders`):

```bash
shop_gql '
{
  orders(first: 20, reverse: true, query: "financial_status:paid") {
    edges { node {
      id name createdAt displayFinancialStatus displayFulfillmentStatus
      totalPriceSet { shopMoney { amount currencyCode } }
      customer { id displayName email }
      lineItems(first: 10) { edges { node { title quantity sku } } }
    } }
  }
}' | jq
```

Useful filters: `financial_status:paid|pending|refunded`,
`fulfillment_status:unfulfilled|fulfilled`, `created_at:>2025-01-01`,
`tag:gift`, `email:foo@example.com`.

Single order with address:

```bash
shop_gql '
query($id: ID!) {
  order(id: $id) {
    id name email
    shippingAddress { name address1 address2 city province country zip phone }
    lineItems(first: 50) { edges { node { title quantity variant { sku } originalUnitPriceSet { shopMoney { amount currencyCode } } } } }
    transactions { id kind status amountSet { shopMoney { amount currencyCode } } }
  }
}' '{"id":"gid://shopify/Order/...."}' | jq
```

### 5. Customers

```bash
# Search
shop_gql '
{
  customers(first: 10, query: "email:*@example.com") {
    edges { node { id email displayName numberOfOrders amountSpent { amount currencyCode } } }
  }
}'

# Create
shop_gql '
mutation($input: CustomerInput!) {
  customerCreate(input: $input) {
    customer { id email }
    userErrors { field message }
  }
}' '{"input":{"email":"test@example.com","firstName":"Test","lastName":"User","tags":["api-created"]}}'
```

### 6. Inventory

Inventory is on inventory items tied to variants, tracked per location:

```bash
# Get inventory for a variant across all locations
shop_gql '
query($id: ID!) {
  productVariant(id: $id) {
    id sku
    inventoryItem {
      id tracked
      inventoryLevels(first: 10) {
        edges { node { location { id name } quantities(names: ["available","on_hand","committed"]) { name quantity } } }
      }
    }
  }
}' '{"id":"gid://shopify/ProductVariant/..."}'
```

Delta adjust:

```bash
shop_gql '
mutation($input: InventoryAdjustQuantitiesInput!) {
  inventoryAdjustQuantities(input: $input) {
    inventoryAdjustmentGroup { reason changes { name delta } }
    userErrors { field message }
  }
}' '{
  "input": {
    "reason": "correction",
    "name": "available",
    "changes": [{"delta": 5, "inventoryItemId": "gid://shopify/InventoryItem/...", "locationId": "gid://shopify/Location/..."}]
  }
}'
```

Absolute set:

```bash
shop_gql '
mutation($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    inventoryAdjustmentGroup { id }
    userErrors { field message }
  }
}' '{"input":{"reason":"correction","name":"available","ignoreCompareQuantity":true,"quantities":[{"inventoryItemId":"gid://shopify/InventoryItem/...","locationId":"gid://shopify/Location/...","quantity":100}]}}'
```

### 7. Metafields/metaobjects

```bash
# Read
shop_gql '
query($id: ID!) {
  product(id: $id) {
    metafields(first: 10, namespace: "custom") {
      edges { node { key type value } }
    }
  }
}' '{"id":"gid://shopify/Product/..."}'

# Write (works for any owner type)
shop_gql '
mutation($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { id key namespace }
    userErrors { field message code }
  }
}' '{"metafields":[{"ownerId":"gid://shopify/Product/...","namespace":"custom","key":"care_instructions","type":"multi_line_text_field","value":"Wash cold. Tumble dry low."}]}'
```

### 8. Storefront API

Read-only customer-facing endpoint uses a distinct token:

- endpoint: `https://$SHOPIFY_STORE_DOMAIN/api/$SHOPIFY_API_VERSION/graphql.json`
- public auth: `X-Shopify-Storefront-Access-Token: <public token>`; browser-embeddable
- private auth: `Shopify-Storefront-Private-Token: <private token>`; server-only

```bash
curl -sS -X POST \
  "https://${SHOPIFY_STORE_DOMAIN}/api/${SHOPIFY_API_VERSION:-2026-01}/graphql.json" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Storefront-Access-Token: ${SHOPIFY_STOREFRONT_TOKEN}" \
  -d '{"query":"{ shop { name } products(first: 5) { edges { node { id title handle } } } }"}' | jq
```

### 9. Bulk operations

For catalogs/order dumps larger than rate limits:

```bash
# 1. Start bulk query
shop_gql '
mutation {
  bulkOperationRunQuery(query: """
    { products { edges { node { id title handle variants { edges { node { sku price } } } } } } }
  """) {
    bulkOperation { id status }
    userErrors { field message }
  }
}'

# 2. Poll status
shop_gql '{ currentBulkOperation { id status errorCode objectCount fileSize url partialDataUrl } }'

# 3. When status=COMPLETED, download the JSONL file
curl -sS "$URL" > products.jsonl
```

Each JSONL line is a node; nested connections are separate lines with
`__parentId`; reassemble client-side if needed.

### 10. Webhooks

```bash
shop_gql '
mutation($topic: WebhookSubscriptionTopic!, $sub: WebhookSubscriptionInput!) {
  webhookSubscriptionCreate(topic: $topic, webhookSubscription: $sub) {
    webhookSubscription { id topic endpoint { __typename ... on WebhookHttpEndpoint { callbackUrl } } }
    userErrors { field message }
  }
}' '{"topic":"ORDERS_CREATE","sub":{"callbackUrl":"https://example.com/webhook","format":"JSON"}}'
```

Verify incoming HMAC with app client secret, not access token:

```bash
echo -n "$REQUEST_BODY" | openssl dgst -sha256 -hmac "$APP_SECRET" -binary | base64
# Compare to X-Shopify-Hmac-Sha256 header
```

## Pitfalls

- REST still exists but is frozen; use GraphQL for new admin integrations.
- Admin tokens begin `shpat_`; Storefront public tokens `shpua_`; wrong header produces opaque 401.
- Valid token + 403 means missing scope; Shopify may return `{"errors":[{"message":"Access denied for ..."}]}`; update scopes and reinstall to regenerate token.
- Empty `userErrors` is not sufficient; also require `data.<mutation>.<resource>` non-null and inspect full response.
- GraphQL needs full GID; convert numeric legacy ID as `gid://shopify/Product/<numeric>`.
- Deep `products(first: 250)` can cost 1000+ points; read `extensions.cost`, start narrow, back off.
- `products(first: N, reverse: true)` sorts by `id DESC`; for newest use `sortKey: CREATED_AT, reverse: true`.
- Without `read_all_orders`, orders silently cap at 60-day window; Plus merchants may request protected-data scope.
- Money amounts are strings (`"49.00"`); do not blindly `jq tonumber` when zero-padding matters.
- Multi-currency fields include `shopMoney` and `presentmentMoney`; choose consistently.
- Never put tokens in chat, logs, source, or durable notes.

## Safety

Mutations are real production changes: product create/delete, refunds,
order cancellation, fulfillment, and inventory. Before `productDelete`,
`orderCancel`, `refundCreate`, or bulk mutation, state what changes, which shop,
and obtain user confirmation. No staging clone exists unless user has a separate
development store. Verify `errors`, `userErrors`, resource non-null, and cost
before reporting success.