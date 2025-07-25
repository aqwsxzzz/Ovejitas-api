import { FindOptions } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';
import { AnimalMeasurementModel } from './animal-measurement.model';

export class AnimalMeasurementService extends BaseService {
	private static readonly ALLOWED_ORDERS = OrderParser.createConfig({
		measuredAt: {
			attribute: 'measuredAt',
		},

	} satisfies TypedOrderConfig);

	async getAnimalMeasurements(animalId: number, order?: string): Promise<AnimalMeasurementModel[]> {
		const findOptions: FindOptions = { where: { animalId } };
		if (order) {
			// Validate orders before parsing
			this.validateOrder(order, AnimalMeasurementService.ALLOWED_ORDERS);
			findOptions.order = this.parseOrder(order, AnimalMeasurementService.ALLOWED_ORDERS);
		}
		return await this.db.models.AnimalMeasurement.findAll(findOptions);
	}
}
