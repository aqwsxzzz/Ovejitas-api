import { BaseService } from '../../services/base.service';
import { FinancialTransactionModel } from './financial-transaction.model';
import {
	FinancialTransactionCreate,
	FinancialTransactionUpdate,
	FinancialTransactionQuery,
	FinancialTransactionSummaryQuery,
	TransactionType,
	SummaryGroupByValue,
} from './financial-transaction.schema';
import { decodeId } from '../../utils/id-hash-util';
import { FindOptions, Op, QueryTypes } from 'sequelize';
import { FilterConfig, FilterConfigBuilder } from '../../utils/filter-parser';
import { PaginatedResult, PaginationParams } from '../../utils/pagination';

interface SummaryTotals {
	income: number;
	expenses: number;
	net: number;
}

interface SummaryBreakdownItem {
	period: string;
	income: number;
	expenses: number;
	net: number;
}

interface SummaryResult {
	totals: SummaryTotals;
	breakdown: SummaryBreakdownItem[];
}

export class FinancialTransactionService extends BaseService {

	private static readonly ALLOWED_FILTERS: FilterConfig = {
		type: FilterConfigBuilder.enum('type', Object.values(TransactionType)),
	};

	async getTransactions(
		farmId: number,
		query?: FinancialTransactionQuery,
		pagination?: PaginationParams,
	): Promise<PaginatedResult<FinancialTransactionModel>> {
		const rawFilterParams = query ? this.extractFilterParams(query as Record<string, unknown>) : undefined;
		// Remove params handled manually below so parseFilters doesn't reject them
		const filterParams = rawFilterParams ? Object.fromEntries(
			Object.entries(rawFilterParams).filter(([k]) => !['from', 'to', 'speciesId'].includes(k)),
		) : undefined;
		const filterWhere = this.parseFilters(filterParams, FinancialTransactionService.ALLOWED_FILTERS);

		const where: Record<string, unknown> = {
			farmId,
			...filterWhere,
		};

		// Handle speciesId filter
		if (query?.speciesId) {
			const decodedSpeciesId = decodeId(query.speciesId);
			if (decodedSpeciesId) {
				where.speciesId = decodedSpeciesId;
			}
		}

		// Handle date range filters
		if (query?.from || query?.to) {
			const dateCondition: Record<symbol, string> = {};
			if (query.from) dateCondition[Op.gte] = query.from;
			if (query.to) dateCondition[Op.lte] = query.to;
			where.date = dateCondition;
		}

		const findOptions: FindOptions = { where };

		return this.findAllPaginated(
			this.db.sequelize.models.FinancialTransaction as typeof FinancialTransactionModel,
			findOptions,
			pagination!,
		);
	}

	async getTransactionById(id: number, farmId: number): Promise<FinancialTransactionModel | null> {
		const transaction = await this.db.sequelize.models.FinancialTransaction.findOne({
			where: { id, farmId },
		}) as FinancialTransactionModel | null;
		return transaction;
	}

	async createTransaction(
		data: FinancialTransactionCreate & { farmId: number; createdBy: number },
	): Promise<FinancialTransactionModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			const decodedSpeciesId = decodeId(data.speciesId);
			if (!decodedSpeciesId) {
				throw new Error('Invalid species ID');
			}

			// Validate species exists
			const species = await this.db.models.Species.findByPk(decodedSpeciesId, { transaction });
			if (!species) {
				throw new Error('Species not found');
			}

			const result = await this.db.sequelize.models.FinancialTransaction.create(
				{
					...data,
					speciesId: decodedSpeciesId,
				},
				{ transaction },
			) as FinancialTransactionModel;
			return result;
		});
	}

	async updateTransaction(
		id: number,
		farmId: number,
		data: FinancialTransactionUpdate,
	): Promise<FinancialTransactionModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const existing = await this.db.sequelize.models.FinancialTransaction.findOne({
				where: { id, farmId },
				transaction,
			}) as FinancialTransactionModel | null;

			if (!existing) {
				return null;
			}

			const processedData: Record<string, unknown> = { ...data };

			if (data.speciesId) {
				const decodedSpeciesId = decodeId(data.speciesId);
				if (!decodedSpeciesId) {
					throw new Error('Invalid species ID');
				}
				const species = await this.db.models.Species.findByPk(decodedSpeciesId, { transaction });
				if (!species) {
					throw new Error('Species not found');
				}
				processedData.speciesId = decodedSpeciesId;
			}

			await existing.update(processedData, { transaction });
			return existing;
		});
	}

	async deleteTransaction(id: number, farmId: number): Promise<boolean> {
		const result = await this.db.sequelize.models.FinancialTransaction.destroy({
			where: { id, farmId },
		});
		return result > 0;
	}

	async getSummary(farmId: number, query: FinancialTransactionSummaryQuery): Promise<SummaryResult> {
		const { from, to } = this.resolveDateRange(query);
		const groupBy = query.groupBy ?? 'month';

		const where: Record<string, unknown> = {
			farmId,
			date: {
				[Op.gte]: from,
				[Op.lte]: to,
			},
		};

		if (query.type) {
			where.type = query.type;
		}

		if (query.speciesId) {
			const decodedSpeciesId = decodeId(query.speciesId);
			if (decodedSpeciesId) {
				where.speciesId = decodedSpeciesId;
			}
		}

		const dateExpression = this.getDateGroupExpression(groupBy);

		const results = await this.db.sequelize.query<{
			period: string;
			type: string;
			total: string;
		}>(
			`SELECT ${dateExpression} as period, type, SUM(amount) as total
			 FROM financial_transactions
			 WHERE farm_id = :farmId
			   AND date >= :from
			   AND date <= :to
			   ${query.type ? 'AND type = :type' : ''}
			   ${query.speciesId ? 'AND species_id = :speciesId' : ''}
			 GROUP BY period, type
			 ORDER BY period ASC`,
			{
				replacements: {
					farmId,
					from,
					to,
					...(query.type && { type: query.type }),
					...(query.speciesId && { speciesId: decodeId(query.speciesId) }),
				},
				type: QueryTypes.SELECT,
			},
		);

		return this.buildSummaryFromResults(results);
	}

	private resolveDateRange(query: FinancialTransactionSummaryQuery): { from: string; to: string } {
		if (query.from && query.to) {
			return { from: query.from, to: query.to };
		}

		const now = new Date();
		const to = query.to ?? now.toISOString().split('T')[0]!;

		if (query.period) {
			const match = query.period.match(/^(\d+)(d|w|m|y)$/);
			if (!match) {
				throw new Error('Invalid period format. Use format like 7d, 4w, 3m, 1y');
			}

			const value = parseInt(match[1]!, 10);
			const unit = match[2]!;
			const fromDate = new Date(now);

			switch (unit) {
			case 'd':
				fromDate.setDate(fromDate.getDate() - value);
				break;
			case 'w':
				fromDate.setDate(fromDate.getDate() - (value * 7));
				break;
			case 'm':
				fromDate.setMonth(fromDate.getMonth() - value);
				break;
			case 'y':
				fromDate.setFullYear(fromDate.getFullYear() - value);
				break;
			}

			return { from: query.from ?? fromDate.toISOString().split('T')[0]!, to };
		}

		// Default to last 30 days
		const fromDate = new Date(now);
		fromDate.setDate(fromDate.getDate() - 30);
		return { from: query.from ?? fromDate.toISOString().split('T')[0]!, to };
	}

	private getDateGroupExpression(groupBy: SummaryGroupByValue): string {
		switch (groupBy) {
		case 'day':
			return 'TO_CHAR(date, \'YYYY-MM-DD\')';
		case 'week':
			return 'TO_CHAR(DATE_TRUNC(\'week\', date), \'YYYY-MM-DD\')';
		case 'month':
			return 'TO_CHAR(date, \'YYYY-MM\')';
		case 'year':
			return 'TO_CHAR(date, \'YYYY\')';
		}
	}

	private buildSummaryFromResults(
		results: Array<{ period: string; type: string; total: string }>,
	): SummaryResult {
		const periodMap = new Map<string, { income: number; expenses: number }>();

		let totalIncome = 0;
		let totalExpenses = 0;

		for (const row of results) {
			const amount = Number(row.total);
			const existing = periodMap.get(row.period) ?? { income: 0, expenses: 0 };

			if (row.type === 'income') {
				existing.income += amount;
				totalIncome += amount;
			} else {
				existing.expenses += amount;
				totalExpenses += amount;
			}

			periodMap.set(row.period, existing);
		}

		const breakdown: SummaryBreakdownItem[] = [];
		for (const [period, values] of periodMap) {
			breakdown.push({
				period,
				income: values.income,
				expenses: values.expenses,
				net: values.income - values.expenses,
			});
		}

		return {
			totals: {
				income: totalIncome,
				expenses: totalExpenses,
				net: totalIncome - totalExpenses,
			},
			breakdown,
		};
	}
}
