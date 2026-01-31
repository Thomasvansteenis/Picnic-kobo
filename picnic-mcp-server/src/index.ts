#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import PicnicAPI from "picnic-api";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { createServer } from "http";

// Configuration from environment variables
const config = {
  username: process.env.PICNIC_USERNAME || "",
  password: process.env.PICNIC_PASSWORD || "",
  countryCode: process.env.PICNIC_COUNTRY_CODE || "NL",
  httpPort: parseInt(process.env.HTTP_PORT || "3000"),
  httpHost: process.env.HTTP_HOST || "0.0.0.0",
  enableHttpServer: process.env.ENABLE_HTTP_SERVER === "true",
};

console.log("Starting Picnic MCP Server...");
console.log(`Country: ${config.countryCode}`);
console.log(`HTTP Server: ${config.enableHttpServer ? `Enabled on ${config.httpHost}:${config.httpPort}` : "Disabled"}`);

// Initialize Picnic API client
let picnicClient: any = null;

async function initializePicnicClient() {
  if (!config.username || !config.password) {
    throw new Error("PICNIC_USERNAME and PICNIC_PASSWORD environment variables are required");
  }

  try {
    picnicClient = new PicnicAPI({
      authKey: config.username,
      countryCode: config.countryCode as any,
    });

    await picnicClient.login(config.password);
    console.log("Successfully authenticated with Picnic API");
    return picnicClient;
  } catch (error) {
    console.error("Failed to initialize Picnic client:", error);
    throw error;
  }
}

// Define Zod schemas for tool parameters
const SearchProductsSchema = z.object({
  query: z.string().describe("Search query for products"),
});

const GetCartSchema = z.object({});

const AddToCartSchema = z.object({
  productId: z.string().describe("Product ID to add to cart"),
  count: z.number().default(1).describe("Quantity to add"),
});

const RemoveFromCartSchema = z.object({
  productId: z.string().describe("Product ID to remove from cart"),
  count: z.number().default(1).describe("Quantity to remove"),
});

const ClearCartSchema = z.object({});

const GetUserSchema = z.object({});

const GetDeliveriesSchema = z.object({});

const GetListsSchema = z.object({});

const GetCategoriesSchema = z.object({});

// Helper function to convert Zod schema to JSON schema
function zodToToolInput(schema: z.ZodType<any>): any {
  return zodToJsonSchema(schema) as any;
}

// Define available tools
const tools: Tool[] = [
  {
    name: "search_products",
    description: "Search for products in the Picnic catalog using a search query",
    inputSchema: zodToToolInput(SearchProductsSchema),
  },
  {
    name: "get_cart",
    description: "Get the current shopping cart contents with all items and total price",
    inputSchema: zodToToolInput(GetCartSchema),
  },
  {
    name: "add_to_cart",
    description: "Add a product to the shopping cart by product ID and quantity",
    inputSchema: zodToToolInput(AddToCartSchema),
  },
  {
    name: "remove_from_cart",
    description: "Remove a product from the shopping cart by product ID and quantity",
    inputSchema: zodToToolInput(RemoveFromCartSchema),
  },
  {
    name: "clear_cart",
    description: "Remove all items from the shopping cart",
    inputSchema: zodToToolInput(ClearCartSchema),
  },
  {
    name: "get_user",
    description: "Get user account information including name, email, and address",
    inputSchema: zodToToolInput(GetUserSchema),
  },
  {
    name: "get_deliveries",
    description: "Get delivery slots and scheduled deliveries",
    inputSchema: zodToToolInput(GetDeliveriesSchema),
  },
  {
    name: "get_lists",
    description: "Get user's shopping lists",
    inputSchema: zodToToolInput(GetListsSchema),
  },
  {
    name: "get_categories",
    description: "Get product categories and subcategories",
    inputSchema: zodToToolInput(GetCategoriesSchema),
  },
];

// Create MCP server instance
const server = new Server(
  {
    name: "picnic-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle list_tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Handle call_tool request
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // Ensure client is initialized
    if (!picnicClient) {
      await initializePicnicClient();
    }

    switch (name) {
      case "search_products": {
        const { query } = SearchProductsSchema.parse(args);
        const results = await picnicClient.search(query);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case "get_cart": {
        const cart = await picnicClient.getShoppingCart();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(cart, null, 2),
            },
          ],
        };
      }

      case "add_to_cart": {
        const { productId, count } = AddToCartSchema.parse(args);
        await picnicClient.addProductToShoppingCart(productId, count);
        const cart = await picnicClient.getShoppingCart();
        return {
          content: [
            {
              type: "text",
              text: `Added ${count}x product ${productId} to cart.\n\n${JSON.stringify(cart, null, 2)}`,
            },
          ],
        };
      }

      case "remove_from_cart": {
        const { productId, count } = RemoveFromCartSchema.parse(args);
        await picnicClient.removeProductFromShoppingCart(productId, count);
        const cart = await picnicClient.getShoppingCart();
        return {
          content: [
            {
              type: "text",
              text: `Removed ${count}x product ${productId} from cart.\n\n${JSON.stringify(cart, null, 2)}`,
            },
          ],
        };
      }

      case "clear_cart": {
        await picnicClient.clearShoppingCart();
        return {
          content: [
            {
              type: "text",
              text: "Shopping cart cleared successfully",
            },
          ],
        };
      }

      case "get_user": {
        const user = await picnicClient.getUserDetails();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(user, null, 2),
            },
          ],
        };
      }

      case "get_deliveries": {
        const deliveries = await picnicClient.getDeliveries();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(deliveries, null, 2),
            },
          ],
        };
      }

      case "get_lists": {
        const lists = await picnicClient.getLists();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(lists, null, 2),
            },
          ],
        };
      }

      case "get_categories": {
        const categories = await picnicClient.getCategories();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(categories, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: "text",
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server based on configuration
async function main() {
  try {
    // Initialize Picnic client
    await initializePicnicClient();

    if (config.enableHttpServer) {
      // HTTP Server mode (for Home Assistant addon)
      const httpServer = createServer(async (req, res) => {
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        res.setHeader("Access-Control-Allow-Headers", "Content-Type");

        if (req.method === "OPTIONS") {
          res.writeHead(200);
          res.end();
          return;
        }

        if (req.method === "GET" && req.url === "/health") {
          res.writeHead(200);
          res.end(JSON.stringify({ status: "ok", version: "1.0.0" }));
          return;
        }

        if (req.method === "GET" && req.url === "/tools") {
          res.writeHead(200);
          res.end(JSON.stringify({ tools }));
          return;
        }

        if (req.method === "POST" && req.url === "/call-tool") {
          let body = "";
          req.on("data", (chunk) => {
            body += chunk.toString();
          });

          req.on("end", async () => {
            try {
              const { name, arguments: args } = JSON.parse(body);
              const response = await server.request(
                { method: "tools/call", params: { name, arguments: args } },
                CallToolRequestSchema
              );
              res.writeHead(200);
              res.end(JSON.stringify(response));
            } catch (error) {
              const errorMessage = error instanceof Error ? error.message : String(error);
              res.writeHead(500);
              res.end(JSON.stringify({ error: errorMessage }));
            }
          });
          return;
        }

        res.writeHead(404);
        res.end(JSON.stringify({ error: "Not found" }));
      });

      httpServer.listen(config.httpPort, config.httpHost, () => {
        console.log(`HTTP Server listening on http://${config.httpHost}:${config.httpPort}`);
        console.log(`Health check: http://${config.httpHost}:${config.httpPort}/health`);
      });
    } else {
      // Stdio mode (for MCP clients like Claude Desktop)
      const transport = new StdioServerTransport();
      await server.connect(transport);
      console.log("Picnic MCP Server running on stdio");
    }
  } catch (error) {
    console.error("Failed to start server:", error);
    process.exit(1);
  }
}

main();
