import { encodeId } from '../../utils/id-hash-util';
import { AnimalMeasurementResponse } from './animal-measurement.schema';
import { AnimalMeasurementModel } from './animal-measurement.model';

export class AnimalMeasurementSerializer {
	static serialize(measurement: AnimalMeasurementModel): AnimalMeasurementResponse {
		return {
			id: encodeId(measurement.id),
			animalId: encodeId(measurement.animalId),
			measurementType: measurement.measurementType,
			value: measurement.value,
			unit: measurement.unit,
			measuredAt: measurement.measuredAt,
			measuredBy: encodeId(measurement.measuredBy),
			notes: measurement.notes,
			createdAt: measurement.createdAt,
			updatedAt: measurement.updatedAt,
		};
	}

	static serializeMany(measurements: AnimalMeasurementModel[]): AnimalMeasurementResponse[] {
		return measurements.map(m => this.serialize(m));
	}
}
