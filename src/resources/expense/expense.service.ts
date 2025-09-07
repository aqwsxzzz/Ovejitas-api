import { BaseService } from '../../services/base.service';
import { ExpenseModel } from './expense.model';
import { ExpenseCreate, ExpenseUpdate, ExpenseQuery, ExpenseCategory, PaymentMethod, ExpenseStatus } from './expense.schema';
import { decodeId } from '../../utils/id-hash-util';
import { FindOptions, Transaction } from 'sequelize';
import { FilterConfig, FilterConfigBuilder } from '../../utils/filter-parser';

export class ExpenseService extends BaseService {

	private static readonly ALLOWED_FILTERS: FilterConfig = {
		category: FilterConfigBuilder.enum('category', Object.values(ExpenseCategory)),
		paymentMethod: FilterConfigBuilder.enum('paymentMethod', Object.values(PaymentMethod)),
		status: FilterConfigBuilder.enum('status', Object.values(ExpenseStatus)),
	};

	async getExpenses(farmId: number, query?: ExpenseQuery): Promise<ExpenseModel[]> {

		const filterWhere = this.parseFilters(query, ExpenseService.ALLOWED_FILTERS);
		const findOptions: FindOptions = {
			where: {
				farmId,
				...filterWhere,
			},
		};

		const expenses = await this.db.sequelize.models.Expense.findAll(findOptions) as ExpenseModel[];
		return expenses;
	}

	async getExpenseById(id: number, farmId: number): Promise<ExpenseModel | null> {
		const findOptions: FindOptions = {
			where: { id, farmId },
		};

		const expense = await this.db.sequelize.models.Expense.findOne(findOptions) as ExpenseModel | null;
		return expense;
	}

	async createExpense(data: ExpenseCreate & { farmId: number; createdBy: number }): Promise<ExpenseModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			const processedData = await this.processExpenseData(data, transaction);

			// Validate amount calculation if quantity and unitCost are provided
			if (processedData.quantity && processedData.unitCost) {
				const calculatedAmount = Number(processedData.quantity) * Number(processedData.unitCost);
				if (Math.abs(calculatedAmount - Number(processedData.amount)) > 0.01) {
					throw new Error(`Amount (${processedData.amount}) does not match quantity (${processedData.quantity}) × unit cost (${processedData.unitCost}) = ${calculatedAmount}`);
				}
			}

			// Validate that quantityUnit is provided if quantity is provided
			if (processedData.quantity && !processedData.quantityUnit) {
				throw new Error('Quantity unit is required when quantity is provided');
			}

			const expense = await this.db.sequelize.models.Expense.create(processedData, { transaction }) as ExpenseModel;
			return expense;
		});
	}

	async updateExpense(id: number, farmId: number, data: ExpenseUpdate): Promise<ExpenseModel | null> {
		return this.db.sequelize.transaction(async (transaction) => {
			const expense = await this.db.sequelize.models.Expense.findOne({
				where: { id, farmId },
				transaction,
			}) as ExpenseModel | null;

			if (!expense) {
				return null;
			}

			const processedData = await this.processExpenseData(data, transaction);

			// Get the current values for validation
			const currentQuantity = processedData.quantity ?? expense.quantity;
			const currentUnitCost = processedData.unitCost ?? expense.unitCost;
			const currentAmount = processedData.amount ?? expense.amount;

			// Validate amount calculation if quantity and unitCost are both present
			if (currentQuantity && currentUnitCost) {
				const calculatedAmount = Number(currentQuantity) * Number(currentUnitCost);
				if (Math.abs(calculatedAmount - Number(currentAmount)) > 0.01) {
					throw new Error(`Amount (${currentAmount}) does not match quantity (${currentQuantity}) × unit cost (${currentUnitCost}) = ${calculatedAmount}`);
				}
			}

			// Validate that quantityUnit is provided if quantity is provided
			const currentQuantityUnit = processedData.quantityUnit ?? expense.quantityUnit;
			if (currentQuantity && !currentQuantityUnit) {
				throw new Error('Quantity unit is required when quantity is provided');
			}

			await expense.update(processedData, { transaction });
			return expense;
		});
	}

	async deleteExpense(id: number, farmId: number): Promise<boolean> {
		const result = await this.db.sequelize.models.Expense.destroy({
			where: { id, farmId },
		});

		return result > 0;
	}

	private async processExpenseData(data: ExpenseCreate & { farmId: number; createdBy: number } | ExpenseUpdate, transaction: Transaction): Promise<Record<string, unknown>> {
		const processedData: Record<string, unknown> = { ...data };

		// Decode encoded IDs
		if (data.speciesId) {
			processedData.speciesId = decodeId(data.speciesId);
			// Validate species exists
			const species = await this.db.models.Species.findByPk(processedData.speciesId as number, { transaction });
			if (!species) {
				throw new Error('Species not found');
			}
		}

		if (data.breedId) {
			processedData.breedId = decodeId(data.breedId);
			// Validate breed exists and belongs to the species if specified
			const breed = await this.db.models.Breed.findByPk(processedData.breedId as number, { transaction });
			if (!breed) {
				throw new Error('Breed not found');
			}
			if (processedData.speciesId && breed.speciesId !== processedData.speciesId) {
				throw new Error('Breed does not belong to the specified species');
			}
		}

		if (data.animalId) {
			processedData.animalId = decodeId(data.animalId);
			// Validate animal exists and belongs to the farm
			const animal = await this.db.models.Animal.findOne({
				where: {
					id: processedData.animalId as number,
					farmId: (processedData.farmId || (data as ExpenseCreate & { farmId: number }).farmId) as number,
				},
				transaction,
			});
			if (!animal) {
				throw new Error('Animal not found or does not belong to this farm');
			}
		}

		if (data.lotId) {
			processedData.lotId = decodeId(data.lotId);
			// Note: Lot validation would go here when lot management is implemented
		}

		return processedData;
	}
}
