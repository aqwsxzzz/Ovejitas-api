import { encodeId } from '../../utils/id-hash-util';
import { FinancialTransactionResponse } from './financial-transaction.schema';
import { FinancialTransactionModel } from './financial-transaction.model';

export class FinancialTransactionSerializer {
	static serialize(transaction: FinancialTransactionModel): FinancialTransactionResponse {
		return {
			id: encodeId(transaction.id),
			farmId: encodeId(transaction.farmId),
			type: transaction.type as FinancialTransactionResponse['type'],
			amount: Number(transaction.amount),
			description: transaction.description,
			speciesId: encodeId(transaction.speciesId),
			date: transaction.date,
			createdBy: encodeId(transaction.createdBy),
			createdAt: transaction.createdAt,
			updatedAt: transaction.updatedAt,
		};
	}

	static serializeMany(transactions: FinancialTransactionModel[]): FinancialTransactionResponse[] {
		return transactions.map(transaction => this.serialize(transaction));
	}
}
