import { Farm } from "./farm-model";
import { User } from "./user-model";
import { FarmMembers } from "./farm-members-model";
import { Species } from "./species-model";
import { SpeciesTranslation } from "./species-translation-model";

// Farm & FarmMembers
FarmMembers.belongsTo(Farm, { foreignKey: "farmId", as: "farm" });
FarmMembers.belongsTo(User, { foreignKey: "userId", as: "user" });
Farm.hasMany(FarmMembers, { foreignKey: "farmId", as: "members" });
User.hasMany(FarmMembers, { foreignKey: "userId", as: "farmMemberships" });

// Species & SpeciesTranslation
Species.hasMany(SpeciesTranslation, { foreignKey: "speciesId", as: "translations" });
SpeciesTranslation.belongsTo(Species, { foreignKey: "speciesId", as: "species" });
