const { DataTypes } = require("sequelize");

const UserRole = {
	USER: "user",
	ADMIN: "admin",
};

module.exports = {
	/**
	 * @param {import('sequelize').QueryInterface} queryInterface
	 */
	up: async (queryInterface) => {
		await queryInterface.createTable("users", {
			id: {
				type: DataTypes.INTEGER.UNSIGNED,
				autoIncrement: true,
				primaryKey: true,
				allowNull: false,
			},
			display_name: {
				type: DataTypes.STRING,
				allowNull: false,
			},
			email: {
				type: DataTypes.STRING,
				allowNull: false,
				unique: true,
			},
			password: {
				type: DataTypes.STRING,
				allowNull: false,
			},
			is_active: {
				type: DataTypes.BOOLEAN,
				allowNull: false,
				defaultValue: true,
			},
			role: {
				type: DataTypes.ENUM(UserRole.USER, UserRole.ADMIN),
				allowNull: false,
				defaultValue: UserRole.USER,
			},
			created_at: {
				type: DataTypes.DATE,
				allowNull: false,
				defaultValue: DataTypes.NOW,
			},
			updated_at: {
				type: DataTypes.DATE,
				allowNull: false,
				defaultValue: DataTypes.NOW,
			},
		});
	},
	/**
	 * @param {import('sequelize').QueryInterface} queryInterface
	 */
	down: async (queryInterface) => {
		await queryInterface.dropTable("users");
	},
};
