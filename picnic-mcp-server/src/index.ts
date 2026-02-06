/**
 * This is the main server file for the Picnic MCP (Master Control Program).
 * It acts as a bridge between the Home Assistant addon and the Picnic API,
 * providing a simplified and authenticated interface for frontend components.
 */

import { MCP, registerTool } from './mcp';
import { PicnicClient, Product } from './picnic-client';
import { MemoryCache } from './cache';
import { object, string, number, optional } from 'zod';

// --- Types ---

interface AuthData {
  token: string;
}

// --- Main Server Class ---

class PicnicMCP extends MCP {
  private picnic: PicnicClient;
  private cache = new MemoryCache();

  constructor(options: any) {
    super(options);
    this.picnic = new PicnicClient({
      countryCode: this.config.country_code || 'NL',
      authKey: this.config.auth_key,
    });
    console.log('Picnic MCP initialized');
  }

  protected async authenticate(authData: AuthData): Promise<any> {
    if (authData.token) {
      this.picnic.setAuthKey(authData.token);
    }
    const user = await this.picnic.getCurrentUser();
    return user;
  }

  // --- Tool Registration ---

  @registerTool({
    name: 'get_user_profile',
    description: 'Get the user profile information.',
    inputSchema: object({}),
  })
  async getUserProfile() {
    console.log('Tool: getUserProfile');
    return this.picnic.getCurrentUser();
  }

  @registerTool({
    name: 'get_cart',
    description: 'Get the current shopping cart.',
    inputSchema: object({}),
  })
  async getCart() {
    console.log('Tool: get_cart');
    return this.picnic.getCart();
  }

  @registerTool({
    name: 'add_to_cart',
    description: 'Add a product to the cart. Returns the updated cart.',
    inputSchema: object({
      productId: string().describe('The ID of the product to add.'),
      count: number().default(1).describe('The number of items to add.'),
    }),
  })
  async addToCart({ productId, count }: { productId: string; count: number }) {
    console.log('Tool: add_to_cart', { productId, count });
    await this.picnic.addProductToCart(productId, count);
    return this.picnic.getCart();
  }

  @registerTool({
    name: 'remove_from_cart',
    description: 'Remove a product from the cart. Returns the updated cart.',
    inputSchema: object({
      productId: string().describe('The ID of the product to remove.'),
      count: number().default(1).describe('The number of items to remove.'),
    }),
  })
  async removeFromCart({ productId, count }: { productId: string; count: number }) {
    console.log('Tool: remove_from_cart', { productId, count });
    await this.picnic.removeProductFromCart(productId, count);
    return this.picnic.getCart();
  }

  @registerTool({
    name: 'clear_cart',
    description: 'Clear the entire shopping cart. Returns the updated cart.',
    inputSchema: object({}),
  })
  async clearCart() {
    console.log('Tool: clear_cart');
    await this.picnic.clearCart();
    return this.picnic.getCart();
  }

  @registerTool({
    name: 'search_products',
    description: 'Search for products in the Picnic catalog.',
    inputSchema: object({
      query: string().describe('The search query.'),
    }),
  })
  async searchProducts({ query }: { query: string }) {
    console.log('Tool: search_products', { query });
    return this.picnic.search(query);
  }

  @registerTool({
    name: 'get_product_details',
    description: 'Get details for a specific product.',
    inputSchema: object({
      productId: string().describe('The ID of the product.'),
    }),
  })
  async getProductDetails({ productId }: { productId: string }) {
    console.log('Tool: get_product_details', { productId });
    const products = await this.picnic.getProducts([productId]);
    return products && products.length > 0 ? products[0] : null;
  }

  @registerTool({
    name: 'get_suggestions',
    description: 'Get personalized product suggestions.',
    inputSchema: object({
      limit: number().default(10).describe('The maximum number of suggestions to return.'),
    }),
  })
  async getSuggestions({ limit }: { limit: number }) {
    console.log('Tool: get_suggestions', { limit });
    // This is a simplified implementation. A real one would be more complex.
    const cart = await this.picnic.getCart();
    const lastOrderId = cart?.items?.[0]?.order_id;
    if (!lastOrderId) {
      // Return generic popular items if no order history
      const result = await this.picnic.search('bestsellers');
      return result.items.slice(0, limit).map((item: any) => ({
        id: item.id,
        name: item.name,
        price: item.price,
        image_url: item.image_id ? this.picnic.getImageUrl(item.image_id) : undefined,
        type: 'suggestion',
      }));
    }

    const order = await this.picnic.getOrder(lastOrderId);
    const productIds = order.items.map((item: any) => item.product_id);
    const products = await this.picnic.getProducts(productIds);
    return products.slice(0, limit).map((p: Product) => ({ ...p, type: 'reorder' }));
  }

  @registerTool({
    name: 'get_delivery_slots',
    description: 'Get available delivery slots.',
    inputSchema: object({}),
  })
  async getDeliverySlots() {
    console.log('Tool: get_delivery_slots');
    return this.picnic.getDeliverySlots();
  }

  @registerTool({
    name: 'select_delivery_slot',
    description: 'Select a delivery slot.',
    inputSchema: object({
      slotId: string().describe('The ID of the slot to select.'),
    }),
  })
  async selectDeliverySlot({ slotId }: { slotId: string }) {
    console.log('Tool: select_delivery_slot', { slotId });
    return this.picnic.selectDeliverySlot(slotId);
  }

  @registerTool({
    name: 'get_order_history',
    description: 'Get past and upcoming orders.',
    inputSchema: object({
      filter: optional(string().enum(['CURRENT', 'COMPLETED'])).describe('Filter orders by status.'),
      limit: optional(number()).describe('Max number of orders to return.'),
      offset: optional(number()).describe('Offset for pagination.'),
    }),
  })
  async get_order_history({
    filter,
    limit,
    offset,
  }: {
    filter?: 'CURRENT' | 'COMPLETED';
    limit?: number;
    offset?: number;
  }) {
    console.log('Tool: get_order_history', { filter, limit, offset });
    let deliveries = [...(await this.getPastDeliveries()), ...(await this.getUpcomingDeliveries())];

    if (filter) {
      deliveries = deliveries.filter(d => d.status === filter);
    }
    
    const total = deliveries.length;
    
    if (offset) {
      deliveries = deliveries.slice(offset);
    }
    if (limit) {
      deliveries = deliveries.slice(0, limit);
    }

    return { deliveries, total, has_more: (offset || 0) + (limit || 0) < total };
  }

  @registerTool({
    name: 'get_delivery_details',
    description: 'Get details for a specific delivery.',
    inputSchema: object({
      deliveryId: string().describe('The ID of the delivery.'),
    }),
  })
  async getDeliveryDetails({ deliveryId }: { deliveryId: string }) {
    console.log('Tool: get_delivery_details', { deliveryId });
    return this.picnic.getDelivery(deliveryId);
  }

  @registerTool({
    name: 'checkout',
    description: 'Checkout the current cart.',
    inputSchema: object({}),
  })
  async checkout() {
    console.log('Tool: checkout');
    return this.picnic.checkout();
  }
  
  @registerTool({
    name: 'get_lists',
    description: 'Retrieve all shopping lists.',
    inputSchema: object({}),
  })
  async getLists() {
    console.log('Tool: get_lists');
    return this.picnic.getLists();
  }

  @registerTool({
    name: 'get_list_details',
    description: 'Get the details and items of a specific shopping list.',
    inputSchema: object({
      listId: string().describe('The ID of the shopping list.'),
    }),
  })
  async getListDetails({ listId }: { listId: string }) {
    console.log('Tool: get_list_details', { listId });
    return this.picnic.getList(listId);
  }

  @registerTool({
    name: 'add_product_to_list',
    description: 'Add a product to a specific shopping list.',
    inputSchema: object({
      listId: string().describe('The ID of the shopping list.'),
      productId: string().describe('The ID of the product to add.'),
    }),
  })
  async addProductToList({ listId, productId }: { listId: string; productId: string }) {
    console.log('Tool: add_product_to_list', { listId, productId });
    const list = await this.picnic.getList(listId);
    const productIds = list.items.map((i: any) => i.id);
    if (!productIds.includes(productId)) {
      productIds.push(productId);
      return this.picnic.updateList(listId, { items: productIds.map(id => ({ id, type: 'PRODUCT' })) });
    }
    return list;
  }
  
  @registerTool({
    name: 'remove_product_from_list',
    description: 'Remove a product from a specific shopping list.',
    inputSchema: object({
      listId: string().describe('The ID of the shopping list.'),
      productId: string().describe('The ID of the product to remove.'),
    }),
  })
  async removeProductFromList({ listId, productId }: { listId: string; productId: string }) {
    console.log('Tool: remove_product_from_list', { listId, productId });
    const list = await this.picnic.getList(listId);
    const productIds = list.items.map((i: any) => i.id).filter((id: string) => id !== productId);
    return this.picnic.updateList(listId, { items: productIds.map(id => ({ id, type: 'PRODUCT' })) });
  }

  @registerTool({
    name: 'search_orders',
    description: 'Search for products within past and upcoming orders.',
    inputSchema: object({
      query: string().describe('The product name to search for.'),
      scope: string().enum(['all', 'upcoming', 'history']).default('all').describe('Whether to search in all, upcoming, or past orders.'),
    }),
  })
  async searchOrders({ query, scope }: { query: string; scope: 'all' | 'upcoming' | 'history' }) {
    console.log('Tool: search_orders', { query, scope });
    
    let orders: any[] = [];
    if (scope === 'upcoming' || scope === 'all') {
      orders = orders.concat(await this.getUpcomingDeliveries());
    }
    if (scope === 'history' || scope === 'all') {
      orders = orders.concat(await this.getPastDeliveries());
    }

    const lowerCaseQuery = query.toLowerCase();
    const matches: any[] = [];

    for (const order of orders) {
      const deliveryDetails = await this.picnic.getDelivery(order.id);
      if (deliveryDetails && deliveryDetails.orders) {
        for (const subOrder of deliveryDetails.orders) {
          if (subOrder.items) {
            for (const item of subOrder.items) {
              const baseItem = item.items && item.items[0] ? item.items[0] : item;
              if (baseItem.name && baseItem.name.toLowerCase().includes(lowerCaseQuery)) {
                let quantity = 1;
                if (baseItem.decorators) {
                  for (const decorator of baseItem.decorators) {
                    if (decorator.type === 'QUANTITY') {
                      quantity = decorator.quantity;
                      break;
                    }
                  }
                }
                
                matches.push({
                  orderId: order.id,
                  deliveryDate: order.delivery_time.start,
                  deliveryStatus: order.status,
                  productName: baseItem.name,
                  productId: baseItem.id,
                  quantity: quantity,
                  price: baseItem.price,
                });
              }
            }
          }
        }
      }
    }

    return {
      query,
      scope,
      matches,
    };
  }

  // --- Helper Methods ---

  private async getPastDeliveries() {
    const cacheKey = 'deliveries:past';
    const cached = this.cache.get(cacheKey);
    if (cached) return cached;
    const result = await this.picnic.getDeliveries('COMPLETED');
    this.cache.set(cacheKey, result, 600); // Cache for 10 minutes
    return result;
  }

  private async getUpcomingDeliveries() {
    const cacheKey = 'deliveries:upcoming';
    const cached = this.cache.get(cacheKey);
    if (cached) return cached;
    const result = await this.picnic.getDeliveries('CURRENT');
    this.cache.set(cacheKey, result, 60); // Cache for 1 minute
    return result;
  }
}

// --- Server Initialization ---

const mcp = new PicnicMCP({
  port: 3000,
  configPath: '/data/options.json',
});

mcp.start();
