import { Database } from '../database';
import {  OrderItem } from 'sequelize';

export interface OrderConfigItem {
  model?: string; // Optional - for nested ordering
  as?: string; // For associations
  attribute: string; // The actual column/attribute to order by
  direction?: 'ASC' | 'DESC'; // Default direction if not specified
}

// The main order configuration interface
export interface OrderConfig {
  [orderKey: string]: OrderConfigItem;
}

// Sequelize order item type (simplified)
export type SequelizeOrderItem = OrderItem;

export class OrderParser {
	static parseOrder(
		orderParam: string,
		allowedOrders: OrderConfig,
		db: Database,
	): SequelizeOrderItem[] {
		if (!orderParam) return [];

		this.validateConfig(allowedOrders);

		const requestedOrders = orderParam.split(',').map(o => o.trim());
		const sequelizeOrders: SequelizeOrderItem[] = [];

		for (const order of requestedOrders) {
			// Parse direction (e.g., "name:desc" or just "name")
			const [orderKey, direction] = order.split(':');
			const cleanOrderKey = orderKey.trim();
			const orderDirection = (direction?.trim().toUpperCase() as 'ASC' | 'DESC') || 'ASC';

			// Check if the order is allowed
			if (!allowedOrders[cleanOrderKey]) {
				throw new Error(`Order '${cleanOrderKey}' is not allowed`);
			}

			const config = allowedOrders[cleanOrderKey];

			// Validate direction
			if (!['ASC', 'DESC'].includes(orderDirection)) {
				throw new Error(`Invalid order direction '${orderDirection}'. Must be ASC or DESC`);
			}

			// Use config direction as fallback, then provided direction
			const finalDirection = orderDirection || config.direction || 'ASC';

			let orderItem: SequelizeOrderItem;

			if (config.model && config.as) {
				// Validate that the model exists in the database
				if (!isValidModelName(config.model, db)) {
					throw new Error(`Model '${config.model}' does not exist in database`);
				}

				// Nested ordering (e.g., ordering by associated model)
				orderItem = [
					{ model: db.models[config.model], as: config.as },
					config.attribute,
					finalDirection,
				];
			} else {
				// Simple ordering on current model
				orderItem = [config.attribute, finalDirection];
			}

			sequelizeOrders.push(orderItem);
		}

		return sequelizeOrders;
	}

	static validateConfig<T extends OrderConfig>(config: T): T {
		return config;
	}

	static createConfig<T extends OrderConfig>(config: T): T {
		return this.validateConfig(config);
	}

	/**
	   * Validates that an order parameter only contains allowed orders
	   * @param orderParam - The order parameter string
	   * @param allowedOrders - Configuration of allowed orders
	   * @throws Error if any order is not allowed
	   */
	protected validateOrder(
		orderParam: string | undefined,
		allowedOrders: OrderConfig,
	): void {
		if (!orderParam) return;

		const requestedOrders = orderParam.split(',').map(o => o.trim());

		for (const order of requestedOrders) {
			const [orderKey] = order.split(':');
			const cleanOrderKey = orderKey.trim();

			if (!allowedOrders[cleanOrderKey]) {
				throw new Error(`Order '${cleanOrderKey}' is not allowed for this resource`);
			}
		}
	}
}

function isValidModelName(
	modelName: string,
	db: Database,
): modelName is keyof Database['models'] {
	return modelName in db.models;
}
export type ModelName = keyof Database['models'];

export type TypedOrderConfig = Record<string, OrderConfigItem & {
  model?: ModelName;
}>;
