import { BaseService } from '../../services/base.service';
import { FarmMemberWithFarm } from '../farm-member/farm-member.schema';
import { FarmModel } from './farm.model';
import { FarmCreateInput, FarmUpdateInput } from './farm.schema';

export class FarmService extends BaseService {

	async createFarm(data: FarmCreateInput): Promise<FarmModel> {
		const farm = await this.db.models.Farm.create(data);
		return farm;
	}

	async getFarms(userId: number): Promise<FarmModel[]> {
		const farmMembers = await this.db.models.FarmMember.findAll({
			where: { userId },
			include: [{
				model: FarmModel,
				as: 'farm',
				required: true,
			}],
		}) as FarmMemberWithFarm[];

		return farmMembers.map(member => member.farm);

	}

	async getFarm(farmId: number): Promise<FarmModel> {
		const farm = await this.db.models.Farm.findByPk(farmId);
		if (!farm) {
			throw new Error('Farm not found');
		}
		return farm;

	}

	async updateFarm(farmId: number, data: FarmUpdateInput): Promise<FarmModel> {
		const farm = await this.db.models.Farm.findByPk(farmId);
		if (!farm) {
			throw new Error('Farm not found');
		}
		await farm.update(data);
		return farm;
	}

	async deleteFarm(farmId: number): Promise<void> {
		const farm = await this.db.models.Farm.findByPk(farmId);
		if (!farm) {
			throw new Error('Farm not found');
		}
		await farm.destroy();
	}

}
