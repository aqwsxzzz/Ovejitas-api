import { encodeId } from '../../utils/id-hash-util';
import { ExpenseResponse } from './expense.schema';
import { ExpenseModel } from './expense.model';

export class ExpenseSerializer {
	static serialize(expense: ExpenseModel): ExpenseResponse {
		return {
			id: encodeId(expense.id),
			farmId: encodeId(expense.farmId),
			date: expense.date,
			amount: expense.amount,
			description: expense.description ?? '',
			category: expense.category as ExpenseResponse['category'],
			speciesId: expense.speciesId ? encodeId(expense.speciesId) : undefined,
			breedId: expense.breedId ? encodeId(expense.breedId) : undefined,
			animalId: expense.animalId ? encodeId(expense.animalId) : undefined,
			lotId: expense.lotId ? encodeId(expense.lotId) : undefined,
			vendor: expense.vendor ?? '',
			paymentMethod: expense.paymentMethod as ExpenseResponse['paymentMethod'],
			invoiceNumber: expense.invoiceNumber ?? '',
			quantity: expense.quantity ?? 0,
			quantityUnit: expense.quantityUnit as ExpenseResponse['quantityUnit'],
			unitCost: expense.unitCost ?? 0,
			status: expense.status as ExpenseResponse['status'],
			createdBy: encodeId(expense.createdBy),
			createdAt: expense.createdAt,
			updatedAt: expense.updatedAt,
		};
	}

	static serializeMany(expenses: ExpenseModel[]): ExpenseResponse[] {
		return expenses.map(expense => this.serialize(expense));
	}
}
