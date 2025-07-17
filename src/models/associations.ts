import { Farm } from './farm-model';
import { User } from './user-model';
import { FarmMembers } from './farm-members-model';
import { Species } from './species-model';
import { SpeciesTranslation } from './species-translation-model';
import { Breed } from './breed-model';
import { Animal } from './animal-model';
import { AnimalMeasurement } from './animal-measurement-model';

// Farm & FarmMembers
FarmMembers.belongsTo(Farm, { foreignKey: 'farmId', as: 'farm' });
FarmMembers.belongsTo(User, { foreignKey: 'userId', as: 'user' });
Farm.hasMany(FarmMembers, { foreignKey: 'farmId', as: 'members' });
User.hasMany(FarmMembers, { foreignKey: 'userId', as: 'farmMemberships' });

// Species & SpeciesTranslation
Species.hasMany(SpeciesTranslation, { foreignKey: 'speciesId', as: 'translations' });
SpeciesTranslation.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });

// Species & Breed
Species.hasMany(Breed, { foreignKey: 'speciesId', as: 'breeds' });
Breed.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });

// Animal associations
Animal.belongsTo(Farm, { foreignKey: 'farmId', as: 'farm' });
Animal.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });
Animal.belongsTo(Breed, { foreignKey: 'breedId', as: 'breed' });
Animal.belongsTo(Animal, { foreignKey: 'fatherId', as: 'father' });
Animal.belongsTo(Animal, { foreignKey: 'motherId', as: 'mother' });
Animal.hasMany(Animal, { foreignKey: 'fatherId', as: 'fatheredChildren' });

// AnimalMeasurement associations
AnimalMeasurement.belongsTo(Animal, { foreignKey: 'animalId', as: 'animal' });
AnimalMeasurement.belongsTo(User, { foreignKey: 'measuredBy', as: 'measurer' });
Animal.hasMany(AnimalMeasurement, { foreignKey: 'animalId', as: 'measurements' });
