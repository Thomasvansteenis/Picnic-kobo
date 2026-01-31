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

// Debug: Log raw environment variables
console.log("DEBUG: Raw environment variables:");
console.log(`  PICNIC_USERNAME: ${process.env.PICNIC_USERNAME ? `"${process.env.PICNIC_USERNAME}"` : 'undefined'}`);
console.log(`  PICNIC_PASSWORD: ${process.env.PICNIC_PASSWORD ? `[${process.env.PICNIC_PASSWORD.length} chars]` : 'undefined'}`);
console.log(`  PICNIC_COUNTRY_CODE: ${process.env.PICNIC_COUNTRY_CODE || 'undefined'}`);

// Configuration from environment variables
const config = {
  username: process.env.PICNIC_USERNAME?.trim() || "",
  password: process.env.PICNIC_PASSWORD?.trim() || "",
  countryCode: process.env.PICNIC_COUNTRY_CODE || "NL",
  httpPort: parseInt(process.env.HTTP_PORT || "3000"),
  httpHost: process.env.HTTP_HOST || "0.0.0.0",
  enableHttpServer: process.env.ENABLE_HTTP_SERVER === "true",
};

console.log("Starting Picnic MCP Server...");
console.log(`Username: ${config.username ? config.username : '(not configured)'}`);
console.log(`Password: ${config.password ? '***configured***' : '(not configured)'}`);
console.log(`Country: ${config.countryCode}`);
console.log(`HTTP Server: ${config.enableHttpServer ? `Enabled on ${config.httpHost}:${config.httpPort}` : "Disabled"}`);

// Initialize Picnic API client
let picnicClient: any = null;

async function initializePicnicClient() {
  // Validate credentials
  if (!config.username || config.username.length === 0) {
    const errorMsg = "PICNIC_USERNAME is not configured. Please set your Picnic email in the addon configuration.";
    console.error(errorMsg);
    throw new Error(errorMsg);
  }

  if (!config.password || config.password.length === 0) {
    const errorMsg = "PICNIC_PASSWORD is not configured. Please set your Picnic password in the addon configuration.";
    console.error(errorMsg);
    throw new Error(errorMsg);
  }

  try {
    console.log("Initializing Picnic API client...");
    picnicClient = new PicnicAPI({
      countryCode: config.countryCode as any,
    });

    console.log("Attempting to authenticate with Picnic...");
    await picnicClient.login(config.username, config.password);
    console.log("Successfully authenticated with Picnic API");
    return picnicClient;
  } catch (error) {
    console.error("Failed to initialize Picnic client:", error);
    if (error instanceof Error) {
      if (error.message.includes("Invalid credentials") || error.message.includes("401")) {
        console.error("Authentication failed. Please check your Picnic email and password in the addon configuration.");
      }
    }
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
        try {
          // Try both method names - the API might use getCart() instead of getShoppingCart()
          let cart;
          if (typeof picnicClient.getCart === 'function') {
            cart = await picnicClient.getCart();
          } else if (typeof picnicClient.getShoppingCart === 'function') {
            cart = await picnicClient.getShoppingCart();
          } else {
            throw new Error("Neither getCart() nor getShoppingCart() methods are available on picnicClient");
          }

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(cart, null, 2),
              },
            ],
          };
        } catch (error) {
          console.error("Error in get_cart:", error);
          console.error("Available methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(picnicClient)));
          throw error;
        }
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
          res.end(JSON.stringify({ status: "ok", version: "1.0.9" }));
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
              console.log(`Calling tool: ${name} with args:`, args);

              // Ensure client is initialized
              if (!picnicClient) {
                await initializePicnicClient();
              }

              // Call the tool directly (bypassing MCP Server.request which requires connection)
              let response;

              switch (name) {
                case "search_products": {
                  const { query } = SearchProductsSchema.parse(args);
                  const results = await picnicClient.search(query);
                  console.log("DEBUG: Search results sample (first 2 items):");
                  console.log(JSON.stringify(results?.slice(0, 2), null, 2));
                  response = {
                    content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
                  };
                  break;
                }

                case "get_cart": {
                  let cart;
                  if (typeof picnicClient.getCart === 'function') {
                    cart = await picnicClient.getCart();
                  } else if (typeof picnicClient.getShoppingCart === 'function') {
                    cart = await picnicClient.getShoppingCart();
                  } else {
                    throw new Error("Neither getCart() nor getShoppingCart() methods available");
                  }
                  console.log("DEBUG: Cart data structure:");
                  console.log(JSON.stringify(cart, null, 2).substring(0, 1000) + "...");
                  response = {
                    content: [{ type: "text", text: JSON.stringify(cart, null, 2) }],
                  };
                  break;
                }

                case "add_to_cart": {
                  const { productId, count } = AddToCartSchema.parse(args);
                  await picnicClient.addProductToShoppingCart(productId, count);
                  const cart = await picnicClient.getShoppingCart();
                  response = {
                    content: [{ type: "text", text: `Added ${count}x product ${productId}\n\n${JSON.stringify(cart, null, 2)}` }],
                  };
                  break;
                }

                case "remove_from_cart": {
                  const { productId, count } = RemoveFromCartSchema.parse(args);
                  await picnicClient.removeProductFromShoppingCart(productId, count);
                  const cart = await picnicClient.getShoppingCart();
                  response = {
                    content: [{ type: "text", text: `Removed ${count}x product ${productId}\n\n${JSON.stringify(cart, null, 2)}` }],
                  };
                  break;
                }

                case "clear_cart": {
                  await picnicClient.clearShoppingCart();
                  response = {
                    content: [{ type: "text", text: "Shopping cart cleared successfully" }],
                  };
                  break;
                }

                case "get_user": {
                  const user = await picnicClient.getUserDetails();
                  response = {
                    content: [{ type: "text", text: JSON.stringify(user, null, 2) }],
                  };
                  break;
                }

                case "get_deliveries": {
                  const deliveries = await picnicClient.getDeliveries();
                  response = {
                    content: [{ type: "text", text: JSON.stringify(deliveries, null, 2) }],
                  };
                  break;
                }

                case "get_lists": {
                  const lists = await picnicClient.getLists();
                  response = {
                    content: [{ type: "text", text: JSON.stringify(lists, null, 2) }],
                  };
                  break;
                }

                case "get_categories": {
                  const categories = await picnicClient.getCategories();
                  response = {
                    content: [{ type: "text", text: JSON.stringify(categories, null, 2) }],
                  };
                  break;
                }

                default:
                  throw new Error(`Unknown tool: ${name}`);
              }

              console.log(`Tool ${name} completed successfully`);
              res.writeHead(200);
              res.end(JSON.stringify(response));
            } catch (error) {
              console.error("ERROR in /call-tool endpoint:");
              console.error("Error details:", error);
              console.error("Stack trace:", error instanceof Error ? error.stack : "No stack trace");
              console.error("Request body:", body);

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
