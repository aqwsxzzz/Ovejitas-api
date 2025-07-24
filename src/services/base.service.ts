import { Database } from '../database';
import { IncludeParser, IncludeConfig, SequelizeIncludeObject } from '../utils/include-parser';
import { OrderConfig, OrderParser, SequelizeOrderItem } from '../utils/order-parser';

export abstract class BaseService {
	protected db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	/**
   * Parses include parameters with strict typing
   * @param includeParam - The include parameter string
   * @param allowedIncludes - Configuration of allowed includes for this service
   * @returns Array of Sequelize include objects
   */
	protected parseIncludes(
		includeParam: string | undefined,
		allowedIncludes: IncludeConfig,
	): SequelizeIncludeObject[] {
		if (!includeParam) return [];
		return IncludeParser.parseIncludes(includeParam, allowedIncludes, this.db);
	}

	/**
   * Validates that an include parameter only contains allowed includes
   * @param includeParam - The include parameter string
   * @param allowedIncludes - Configuration of allowed includes
   * @throws Error if any include is not allowed
   */
	protected validateIncludes(
		includeParam: string | undefined,
		allowedIncludes: IncludeConfig,
	): void {
		if (!includeParam) return;

		const requestedIncludes = includeParam.split(',').map(i => i.trim());

		for (const include of requestedIncludes) {
			const mainInclude = include.split('.')[0];
			if (!allowedIncludes[mainInclude]) {
				throw new Error(`Include '${mainInclude}' is not allowed for this resource`);
			}
		}
	}

	/**
   * Parses order parameters with strict typing
   * @param orderParam - The order parameter string (e.g., "name:desc,createdAt:asc")
   * @param allowedOrders - Configuration of allowed orders for this service
   * @returns Array of Sequelize order items
   */
	protected parseOrder(
		orderParam: string | undefined,
		allowedOrders: OrderConfig,
	): SequelizeOrderItem[] {
		if (!orderParam) return [];
		return OrderParser.parseOrder(orderParam, allowedOrders, this.db);
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
