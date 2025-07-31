import { Database } from '../database';
import { IncludeParser, IncludeConfig, SequelizeIncludeObject } from '../utils/include-parser';
import { OrderConfig, OrderParser, SequelizeOrderItem } from '../utils/order-parser';
import { UserLanguage } from '../resources/user/user.schema';
import { FilterConfig, FilterParser, SequelizeWhereOptions } from '../utils/filter-parser';

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
   * Parses filter parameters with strict typing
   * @param filterParams - Object containing filter parameters from query string
   * @param allowedFilters - Configuration of allowed filters for this service
   * @returns Sequelize where options object
   */
	protected parseFilters(
		filterParams: Record<string, string> | undefined,
		allowedFilters: FilterConfig,
	): SequelizeWhereOptions {
		if (!filterParams) return {};
		return FilterParser.parseFilters(filterParams, allowedFilters, this.db);
	}

	/**
   * Filters translation includes by language
   * @param includes - Array of Sequelize include objects
   * @param language - Language to filter by
   * @param translationIncludeName - Name of the translation include (defaults to 'translations')
   * @returns Modified includes array with language filtering applied
   */
	protected filterTranslationsByLanguage(
		includes: SequelizeIncludeObject[],
		language: UserLanguage,
		translationIncludeName: string = 'translations',
	): SequelizeIncludeObject[] {
		return includes.map(include => {
			// Handle direct translation includes
			if (include.as === translationIncludeName) {
				return {
					...include,
					where: { language },
				};
			}

			// Handle nested translation includes
			if (include.include && Array.isArray(include.include)) {
				return {
					...include,
					include: this.filterTranslationsByLanguage(include.include, language, translationIncludeName),
				};
			}

			return include;
		});
	}

	/**
   * Combines multiple where conditions using AND logic
   * @param conditions - Array of where condition objects
   * @returns Combined where options
   */
	protected combineWhereConditions(...conditions: SequelizeWhereOptions[]): SequelizeWhereOptions {
		const combined: SequelizeWhereOptions = {};

		for (const condition of conditions) {
			if (condition && Object.keys(condition).length > 0) {
				Object.assign(combined, condition);
			}
		}

		return combined;
	}

	/**
   * Helper method to extract filter parameters from query string
   * This removes pagination and other non-filter parameters
   * @param query - Full query object from request
   * @param excludeParams - Parameters to exclude from filtering (defaults to common pagination params)
   * @returns Object containing only filter parameters
   */
	public extractFilterParams(
		query: Record<string, unknown>,
	): Record<string, string> {
		const filterParams: Record<string, string> = {};

		const excludeParams = ['page', 'limit', 'include', 'order', 'offset', 'language', 'sort', 'direction'];

		for (const [key, value] of Object.entries(query)) {
			if (!excludeParams.includes(key) && value !== undefined && value !== null) {
				filterParams[key] = String(value);
			}
		}

		return filterParams;
	}
}
