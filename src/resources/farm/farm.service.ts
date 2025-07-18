import { Database } from '../../database';
import { FarmModel } from './farm.model';
import { FarmCreateInput } from './farm.schema';

export class FarmService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async createFarm(data: FarmCreateInput): Promise<FarmModel> {
		const farm = await this.db.models.Farm.create(data);
		return farm;
	}

	async getFarms(): Promise<FarmModel[]> {
		const farms = await this.db.models.Farm.findAll();
		return farms;
	}
}
