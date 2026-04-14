#!/usr/bin/env node
'use strict';

/**
 * Dev seed script — creates a full demo dataset for local development.
 * Run: docker compose exec app node src/scripts/dev-seed.js
 *
 * Creates:
 *   - 1 user (testuser@test.com / Password1)
 *   - 1 farm + owner membership
 *   - 15 animals across all species/breeds
 *   - 40+ measurements (weight, height, temperature) per animal
 *   - Non-feed expenses and income across species
 *   - 2 chicken flocks with flock events and egg collections
 *   - Feed inventory: types, purchase lots (FIFO demo), feeding schedules,
 *     and historical consumption events that span two lots to show the
 *     snapshot cost breakdown. Lot purchases auto-create matching
 *     financial_transactions rows (mirrors FeedLotService behavior).
 */

// eslint-disable-next-line @typescript-eslint/no-require-imports
require('dotenv').config();
const { Sequelize } = require('sequelize');
const bcrypt = require('bcryptjs');

const sequelize = new Sequelize({
	dialect: 'postgres',
	host: process.env.DB_HOST,
	port: Number(process.env.DB_PORT),
	username: process.env.DB_USER,
	password: process.env.DB_PASS,
	database: process.env.DB_NAME,
	logging: false,
});

async function query(sql, replacements) {
	const [rows] = await sequelize.query(sql, { replacements });
	return rows;
}

async function queryOne(sql, replacements) {
	const rows = await query(sql, replacements);
	return rows[0];
}

async function main() {
	await sequelize.authenticate();
	console.log('Connected to database.');

	const now = new Date();

	// --- User (skip if exists) ---
	let existingUser = await queryOne(
		"SELECT id FROM users WHERE email = 'testuser@test.com'",
	);
	let userId;
	let farmId;

	if (existingUser) {
		userId = existingUser.id;
		const existingFarm = await queryOne(
			'SELECT farm_id FROM farm_members WHERE user_id = :userId AND role = \'owner\' LIMIT 1',
			{ userId },
		);
		farmId = existingFarm.farm_id;
		console.log(`User already exists (id: ${userId}, farmId: ${farmId}). Skipping user/farm setup.`);
	} else {
		const hashedPassword = await bcrypt.hash('Password1', 10);
		const user = await queryOne(
			`INSERT INTO users (display_name, email, password, is_active, role, language, created_at, updated_at)
			 VALUES ('Test User', 'testuser@test.com', :password, true, 'user', 'en', :now, :now)
			 RETURNING id`,
			{ password: hashedPassword, now },
		);
		userId = user.id;
		console.log(`Created user (id: ${userId})`);

		const farm = await queryOne(
			`INSERT INTO farms (name, created_at, updated_at)
			 VALUES ('Demo Farm', :now, :now)
			 RETURNING id`,
			{ now },
		);
		farmId = farm.id;
		console.log(`Created farm (id: ${farmId})`);

		await query(
			`INSERT INTO farm_members (farm_id, user_id, role, created_at, updated_at)
			 VALUES (:farmId, :userId, 'owner', :now, :now)`,
			{ farmId, userId, now },
		);

		await query(
			`UPDATE users SET last_visited_farm_id = :farmId WHERE id = :userId`,
			{ farmId, userId },
		);
	}

	// --- Look up species & breed IDs ---
	const speciesRows = await query(
		`SELECT s.id, st.name
		 FROM species s
		 JOIN species_translation st ON st.species_id = s.id
		 WHERE st.language_code = 'en'`,
	);
	const species = {};
	for (const row of speciesRows) {
		species[row.name] = row.id;
	}

	const breedRows = await query(
		`SELECT b.id, b.species_id, bt.name
		 FROM breeds b
		 JOIN breed_translation bt ON bt.breed_id = b.id
		 WHERE bt.language_code = 'en'`,
	);
	const breeds = {};
	for (const row of breedRows) {
		const speciesName = speciesRows.find((s) => s.id === row.species_id)?.name;
		if (speciesName) {
			breeds[`${speciesName}:${row.name}`] = row.id;
		}
	}

	// --- Animals (skip if exists) ---
	const existingAnimals = await queryOne(
		'SELECT COUNT(*) as count FROM animals WHERE farm_id = :farmId',
		{ farmId },
	);

	let animalIds = [];
	if (Number(existingAnimals.count) > 0) {
		const rows = await query(
			`SELECT a.id, a.tag_number as tag FROM animals a WHERE a.farm_id = :farmId`,
			{ farmId },
		);
		animalIds = rows.map((r) => ({ id: r.id, tag: r.tag }));
		console.log(`Animals already exist (${animalIds.length}). Skipping.`);
	} else {
	const animalDefs = [
		// Sheep (5)
		{ name: 'Luna', tag: 'SH-001', species: 'Sheep', breed: 'Suffolk', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2024-03-15' },
		{ name: 'Rex', tag: 'SH-002', species: 'Sheep', breed: 'Merino', sex: 'male', status: 'alive', repro: 'other', acq: 'born', birthDate: '2024-06-01' },
		{ name: 'Dolly', tag: 'SH-003', species: 'Sheep', breed: 'Suffolk', sex: 'female', status: 'alive', repro: 'lactating', acq: 'born', birthDate: '2024-01-10' },
		{ name: 'Wooly', tag: 'SH-004', species: 'Sheep', breed: 'Merino', sex: 'female', status: 'alive', repro: 'open', acq: 'purchased', birthDate: '2023-09-22' },
		{ name: 'Patch', tag: 'SH-005', species: 'Sheep', breed: 'Other', sex: 'male', status: 'sold', repro: 'other', acq: 'born', birthDate: '2024-04-18' },
		// Cattle (4)
		{ name: 'Bessie', tag: 'CA-001', species: 'Cattle', breed: 'Holstein', sex: 'female', status: 'alive', repro: 'lactating', acq: 'purchased', birthDate: '2023-01-20' },
		{ name: 'Bruno', tag: 'CA-002', species: 'Cattle', breed: 'Angus', sex: 'male', status: 'alive', repro: 'other', acq: 'purchased', birthDate: '2023-08-10' },
		{ name: 'Daisy', tag: 'CA-003', species: 'Cattle', breed: 'Holstein', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2022-11-05' },
		{ name: 'Thor', tag: 'CA-004', species: 'Cattle', breed: 'Angus', sex: 'male', status: 'alive', repro: 'other', acq: 'born', birthDate: '2024-02-14' },
		// Goats (3)
		{ name: 'Pepper', tag: 'GO-001', species: 'Goat', breed: 'Boer', sex: 'female', status: 'alive', repro: 'open', acq: 'born', birthDate: '2025-01-05' },
		{ name: 'Clover', tag: 'GO-002', species: 'Goat', breed: 'Saanen', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2024-07-12' },
		{ name: 'Billy', tag: 'GO-003', species: 'Goat', breed: 'Boer', sex: 'male', status: 'alive', repro: 'other', acq: 'purchased', birthDate: '2024-03-30' },
		// Pigs (3)
		{ name: 'Hamlet', tag: 'PI-001', species: 'Pig', breed: 'Yorkshire', sex: 'male', status: 'alive', repro: 'other', acq: 'purchased', birthDate: '2024-11-20' },
		{ name: 'Truffle', tag: 'PI-002', species: 'Pig', breed: 'Duroc', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2024-08-03' },
		{ name: 'Bacon', tag: 'PI-003', species: 'Pig', breed: 'Yorkshire', sex: 'male', status: 'deceased', repro: 'other', acq: 'born', birthDate: '2024-05-15' },
	];

	for (const a of animalDefs) {
		const speciesId = species[a.species];
		const breedId = breeds[`${a.species}:${a.breed}`];
		const animal = await queryOne(
			`INSERT INTO animals (farm_id, species_id, breed_id, name, tag_number, sex, birth_date, status, reproductive_status, acquisition_type, created_at, updated_at)
			 VALUES (:farmId, :speciesId, :breedId, :name, :tag, :sex, :birthDate, :status, :repro, :acq, :now, :now)
			 RETURNING id`,
			{ farmId, speciesId, breedId, name: a.name, tag: a.tag, sex: a.sex, birthDate: a.birthDate, status: a.status, repro: a.repro, acq: a.acq, now },
		);
		animalIds.push({ id: animal.id, ...a });
	}
	console.log(`Created ${animalIds.length} animals`);
	}

	// --- Measurements (skip if exists) ---
	const existingMeasurements = await queryOne(
		'SELECT COUNT(*) as count FROM animal_measurements',
	);

	if (Number(existingMeasurements.count) > 0) {
		console.log('Measurements already exist. Skipping.');
	} else {
	let measurementCount = 0;
	const measurementDefs = [
		// Sheep weights (history over time)
		{ tag: 'SH-001', type: 'weight', value: 58.0, unit: 'kg', daysAgo: 90 },
		{ tag: 'SH-001', type: 'weight', value: 62.3, unit: 'kg', daysAgo: 60 },
		{ tag: 'SH-001', type: 'weight', value: 65.5, unit: 'kg', daysAgo: 30 },
		{ tag: 'SH-001', type: 'weight', value: 68.2, unit: 'kg', daysAgo: 7 },
		{ tag: 'SH-002', type: 'weight', value: 40.0, unit: 'kg', daysAgo: 45 },
		{ tag: 'SH-002', type: 'weight', value: 45.0, unit: 'kg', daysAgo: 14 },
		{ tag: 'SH-003', type: 'weight', value: 70.0, unit: 'kg', daysAgo: 60 },
		{ tag: 'SH-003', type: 'weight', value: 72.5, unit: 'kg', daysAgo: 20 },
		{ tag: 'SH-004', type: 'weight', value: 55.0, unit: 'kg', daysAgo: 30 },
		{ tag: 'SH-004', type: 'weight', value: 57.8, unit: 'kg', daysAgo: 5 },
		{ tag: 'SH-005', type: 'weight', value: 48.0, unit: 'kg', daysAgo: 40 },
		// Cattle weights
		{ tag: 'CA-001', type: 'weight', value: 500.0, unit: 'kg', daysAgo: 60 },
		{ tag: 'CA-001', type: 'weight', value: 520.0, unit: 'kg', daysAgo: 21 },
		{ tag: 'CA-001', type: 'weight', value: 535.0, unit: 'kg', daysAgo: 3 },
		{ tag: 'CA-002', type: 'weight', value: 460.0, unit: 'kg', daysAgo: 45 },
		{ tag: 'CA-002', type: 'weight', value: 480.0, unit: 'kg', daysAgo: 10 },
		{ tag: 'CA-003', type: 'weight', value: 490.0, unit: 'kg', daysAgo: 30 },
		{ tag: 'CA-003', type: 'weight', value: 510.0, unit: 'kg', daysAgo: 5 },
		{ tag: 'CA-004', type: 'weight', value: 350.0, unit: 'kg', daysAgo: 60 },
		{ tag: 'CA-004', type: 'weight', value: 390.0, unit: 'kg', daysAgo: 14 },
		// Goat weights
		{ tag: 'GO-001', type: 'weight', value: 35.0, unit: 'kg', daysAgo: 30 },
		{ tag: 'GO-001', type: 'weight', value: 38.5, unit: 'kg', daysAgo: 5 },
		{ tag: 'GO-002', type: 'weight', value: 42.0, unit: 'kg', daysAgo: 25 },
		{ tag: 'GO-002', type: 'weight', value: 45.0, unit: 'kg', daysAgo: 3 },
		{ tag: 'GO-003', type: 'weight', value: 55.0, unit: 'kg', daysAgo: 20 },
		{ tag: 'GO-003', type: 'weight', value: 58.5, unit: 'kg', daysAgo: 2 },
		// Pig weights
		{ tag: 'PI-001', type: 'weight', value: 95.0, unit: 'kg', daysAgo: 40 },
		{ tag: 'PI-001', type: 'weight', value: 110.0, unit: 'kg', daysAgo: 7 },
		{ tag: 'PI-002', type: 'weight', value: 85.0, unit: 'kg', daysAgo: 35 },
		{ tag: 'PI-002', type: 'weight', value: 98.0, unit: 'kg', daysAgo: 8 },
		{ tag: 'PI-003', type: 'weight', value: 70.0, unit: 'kg', daysAgo: 50 },
		// Heights
		{ tag: 'SH-001', type: 'height', value: 72.0, unit: 'cm', daysAgo: 30 },
		{ tag: 'SH-002', type: 'height', value: 65.0, unit: 'cm', daysAgo: 14 },
		{ tag: 'SH-003', type: 'height', value: 74.0, unit: 'cm', daysAgo: 20 },
		{ tag: 'CA-001', type: 'height', value: 145.0, unit: 'cm', daysAgo: 21 },
		{ tag: 'CA-002', type: 'height', value: 138.0, unit: 'cm', daysAgo: 10 },
		{ tag: 'CA-003', type: 'height', value: 142.0, unit: 'cm', daysAgo: 30 },
		{ tag: 'CA-004', type: 'height', value: 125.0, unit: 'cm', daysAgo: 14 },
		{ tag: 'GO-001', type: 'height', value: 65.0, unit: 'cm', daysAgo: 5 },
		{ tag: 'GO-002', type: 'height', value: 68.0, unit: 'cm', daysAgo: 3 },
		{ tag: 'GO-003', type: 'height', value: 72.0, unit: 'cm', daysAgo: 2 },
		{ tag: 'PI-001', type: 'height', value: 75.0, unit: 'cm', daysAgo: 7 },
		{ tag: 'PI-002', type: 'height', value: 70.0, unit: 'cm', daysAgo: 8 },
		// Temperatures
		{ tag: 'SH-001', type: 'temperature', value: 39.2, unit: 'celsius', daysAgo: 7 },
		{ tag: 'SH-003', type: 'temperature', value: 39.5, unit: 'celsius', daysAgo: 10 },
		{ tag: 'CA-001', type: 'temperature', value: 38.8, unit: 'celsius', daysAgo: 3 },
		{ tag: 'CA-003', type: 'temperature', value: 39.0, unit: 'celsius', daysAgo: 5 },
		{ tag: 'GO-002', type: 'temperature', value: 39.3, unit: 'celsius', daysAgo: 3 },
		{ tag: 'PI-001', type: 'temperature', value: 38.5, unit: 'celsius', daysAgo: 7 },
		{ tag: 'PI-002', type: 'temperature', value: 39.8, unit: 'celsius', daysAgo: 2 },
	];

	for (const m of measurementDefs) {
		const animal = animalIds.find((a) => a.tag === m.tag);
		if (!animal) continue;
		const measuredAt = new Date(now.getTime() - m.daysAgo * 24 * 60 * 60 * 1000);
		const measurement = await queryOne(
			`INSERT INTO animal_measurements (animal_id, measurement_type, value, unit, measured_at, measured_by, created_at, updated_at)
			 VALUES (:animalId, :type, :value, :unit, :measuredAt, :userId, :now, :now)
			 RETURNING id`,
			{ animalId: animal.id, type: m.type, value: m.value, unit: m.unit, measuredAt, userId, now },
		);

		// Link latest weight measurement to animal
		if (m.type === 'weight') {
			await query(
				`UPDATE animals SET weight_id = :measurementId WHERE id = :animalId`,
				{ measurementId: measurement.id, animalId: animal.id },
			);
		}
		measurementCount++;
	}
	console.log(`Created ${measurementCount} measurements`);
	}

	// --- Financial Transactions (skip if exists) ---
	const existingTransactions = await queryOne(
		'SELECT COUNT(*) as count FROM financial_transactions WHERE farm_id = :farmId',
		{ farmId },
	);

	if (Number(existingTransactions.count) > 0) {
		console.log('Financial transactions already exist. Skipping.');
	} else {
	const transactionDefs = [
		// Expenses — Sheep (non-feed; feed expenses are seeded via feed_lots below)
		{ type: 'expense', date: '2025-11-15', amount: 800.00, desc: 'Sheep shearing service', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2025-12-05', amount: 350.00, desc: 'Vaccination - all sheep', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2026-02-05', amount: 280.00, desc: 'Deworming - sheep flock', speciesKey: 'Sheep' },
		// Expenses — Cattle (non-feed)
		{ type: 'expense', date: '2026-01-25', amount: 275.00, desc: 'Hoof trimming - cattle', speciesKey: 'Cattle' },
		{ type: 'expense', date: '2026-02-01', amount: 3200.00, desc: 'New water troughs', speciesKey: 'Cattle' },
		{ type: 'expense', date: '2026-02-15', amount: 600.00, desc: 'Veterinary checkup - cattle', speciesKey: 'Cattle' },
		// Expenses — Goat (non-feed)
		{ type: 'expense', date: '2025-12-15', amount: 450.00, desc: 'Deworming treatment - goats', speciesKey: 'Goat' },
		{ type: 'expense', date: '2026-02-10', amount: 950.00, desc: 'Goat mineral supplements - bulk', speciesKey: 'Goat' },
		// Expenses — Pig (non-feed)
		{ type: 'expense', date: '2026-02-20', amount: 380.00, desc: 'Pig supplements', speciesKey: 'Pig' },
		// Income — Sheep
		{ type: 'income', date: '2025-12-20', amount: 2400.00, desc: 'Wool sale - December batch', speciesKey: 'Sheep' },
		{ type: 'income', date: '2026-01-18', amount: 1800.00, desc: 'Sold 2 lambs at market', speciesKey: 'Sheep' },
		{ type: 'income', date: '2026-03-08', amount: 3200.00, desc: 'Wool sale - March shearing', speciesKey: 'Sheep' },
		// Income — Cattle
		{ type: 'income', date: '2026-01-05', amount: 5500.00, desc: 'Sold 1 steer at auction', speciesKey: 'Cattle' },
		{ type: 'income', date: '2026-02-12', amount: 1200.00, desc: 'Milk sales - February', speciesKey: 'Cattle' },
		{ type: 'income', date: '2026-03-15', amount: 1350.00, desc: 'Milk sales - March', speciesKey: 'Cattle' },
		// Income — Goat
		{ type: 'income', date: '2026-01-22', amount: 900.00, desc: 'Goat cheese sales - January', speciesKey: 'Goat' },
		{ type: 'income', date: '2026-02-25', amount: 1100.00, desc: 'Goat cheese sales - February', speciesKey: 'Goat' },
		{ type: 'income', date: '2026-03-18', amount: 950.00, desc: 'Goat milk sales - March', speciesKey: 'Goat' },
		// Income — Pig
		{ type: 'income', date: '2026-02-08', amount: 4200.00, desc: 'Sold 3 pigs at market', speciesKey: 'Pig' },
		{ type: 'income', date: '2026-03-20', amount: 1500.00, desc: 'Pork pre-orders', speciesKey: 'Pig' },
	];

	let transactionCount = 0;
	for (const t of transactionDefs) {
		const speciesId = species[t.speciesKey];
		await query(
			`INSERT INTO financial_transactions (farm_id, type, amount, description, species_id, date, created_by, created_at, updated_at)
			 VALUES (:farmId, :type, :amount, :desc, :speciesId, :date, :userId, :now, :now)`,
			{
				farmId, type: t.type, amount: t.amount, desc: t.desc,
				speciesId, date: t.date, userId, now,
			},
		);
		transactionCount++;
	}
	console.log(`Created ${transactionCount} financial transactions`);
	}

	// --- Flocks (Chicken) ---
	const chickenSpeciesId = species['Chicken'];
	const chickenBreeds = {};
	for (const [key, id] of Object.entries(breeds)) {
		if (key.startsWith('Chicken:')) {
			chickenBreeds[key.replace('Chicken:', '')] = id;
		}
	}

	const flockDefs = [
		{
			name: 'Layer Flock A',
			breedKey: 'Leghorn',
			flockType: 'layers',
			initialCount: 50,
			currentCount: 47,
			startDate: '2025-10-01',
			acquisitionType: 'purchased',
			houseName: 'Coop 1',
			ageAtAcquisitionWeeks: 18,
			notes: 'First batch of laying hens',
		},
		{
			name: 'Dual Purpose Flock B',
			breedKey: 'Rhode Island Red',
			flockType: 'dual_purpose',
			initialCount: 30,
			currentCount: 28,
			startDate: '2025-11-15',
			acquisitionType: 'purchased',
			houseName: 'Coop 2',
			ageAtAcquisitionWeeks: 16,
			notes: 'Mixed use flock for eggs and meat',
		},
	];

	const flockIds = [];
	const existingFlocks = await queryOne(
		'SELECT COUNT(*) as count FROM flocks WHERE farm_id = :farmId',
		{ farmId },
	);

	if (Number(existingFlocks.count) > 0) {
		const rows = await query(
			'SELECT id, name FROM flocks WHERE farm_id = :farmId ORDER BY id ASC',
			{ farmId },
		);
		for (const row of rows) {
			const def = flockDefs.find((d) => d.name === row.name);
			flockIds.push({ id: row.id, ...(def ?? { name: row.name }) });
		}
		console.log(`Flocks already exist (${flockIds.length}). Skipping flocks, events, egg collections.`);
	} else {
	for (const f of flockDefs) {
		const flock = await queryOne(
			`INSERT INTO flocks (farm_id, species_id, breed_id, name, flock_type, initial_count, current_count, status, start_date, acquisition_type, house_name, age_at_acquisition_weeks, notes, created_at, updated_at)
			 VALUES (:farmId, :speciesId, :breedId, :name, :flockType, :initialCount, :currentCount, 'active', :startDate, :acquisitionType, :houseName, :ageAtAcquisitionWeeks, :notes, :now, :now)
			 RETURNING id`,
			{
				farmId, speciesId: chickenSpeciesId, breedId: chickenBreeds[f.breedKey],
				name: f.name, flockType: f.flockType, initialCount: f.initialCount,
				currentCount: f.currentCount, startDate: f.startDate,
				acquisitionType: f.acquisitionType, houseName: f.houseName,
				ageAtAcquisitionWeeks: f.ageAtAcquisitionWeeks, notes: f.notes, now,
			},
		);
		flockIds.push({ id: flock.id, ...f });
	}
	console.log(`Created ${flockIds.length} flocks`);

	// --- Flock Events ---
	const flockEventDefs = [
		// Layer Flock A: 50 initial → -2 mortality → -1 cull = 47 current
		{ flockIdx: 0, eventType: 'mortality', count: 2, date: '2025-11-10', reason: 'Predator attack' },
		{ flockIdx: 0, eventType: 'cull', count: 1, date: '2025-12-05', reason: 'Sick hen, not recovering' },
		// Dual Purpose Flock B: 30 initial → -1 mortality → -1 sale = 28 current
		{ flockIdx: 1, eventType: 'mortality', count: 1, date: '2025-12-20', reason: 'Unknown cause' },
		{ flockIdx: 1, eventType: 'sale', count: 1, date: '2026-01-15', reason: 'Rooster sold to neighbor' },
	];

	for (const e of flockEventDefs) {
		await query(
			`INSERT INTO flock_events (flock_id, event_type, count, date, reason, recorded_by, created_at, updated_at)
			 VALUES (:flockId, :eventType, :count, :date, :reason, :userId, :now, :now)`,
			{
				flockId: flockIds[e.flockIdx].id, eventType: e.eventType,
				count: e.count, date: e.date, reason: e.reason, userId, now,
			},
		);
	}
	console.log(`Created ${flockEventDefs.length} flock events`);

	// --- Egg Collections ---
	// Generate 14 days of egg data for each flock
	const eggCollections = [];
	for (let daysAgo = 14; daysAgo >= 1; daysAgo--) {
		const date = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000)
			.toISOString().split('T')[0];

		// Layer Flock A: ~85-92% lay rate (47 hens)
		const flockAEggs = 40 + Math.floor(Math.random() * 4);
		const flockABroken = Math.random() < 0.3 ? Math.floor(Math.random() * 3) : 0;
		eggCollections.push({
			flockId: flockIds[0].id, date, totalEggs: flockAEggs,
			brokenEggs: flockABroken, notes: null,
		});

		// Dual Purpose Flock B: ~60-75% lay rate (28 hens)
		const flockBEggs = 17 + Math.floor(Math.random() * 4);
		const flockBBroken = Math.random() < 0.2 ? Math.floor(Math.random() * 2) : 0;
		eggCollections.push({
			flockId: flockIds[1].id, date, totalEggs: flockBEggs,
			brokenEggs: flockBBroken, notes: null,
		});
	}

	for (const ec of eggCollections) {
		await query(
			`INSERT INTO egg_collections (flock_id, date, total_eggs, broken_eggs, collected_by, notes, created_at, updated_at)
			 VALUES (:flockId, :date, :totalEggs, :brokenEggs, :userId, :notes, :now, :now)`,
			{ flockId: ec.flockId, date: ec.date, totalEggs: ec.totalEggs, brokenEggs: ec.brokenEggs, userId, notes: ec.notes, now },
		);
	}
	console.log(`Created ${eggCollections.length} egg collections`);
	}

	// --- Feed Inventory ---
	// Feed types + purchase lots (FIFO demo) + feeding schedules + historical consumption.
	// Lot inserts also write their matching financial_transactions row, mirroring
	// FeedLotService.createFeedLot (snapshotted amount, back-reference via feed_lot_id).
	const existingFeedTypes = await queryOne(
		'SELECT COUNT(*) as count FROM feed_types WHERE farm_id = :farmId',
		{ farmId },
	);

	if (Number(existingFeedTypes.count) > 0) {
		console.log('Feed inventory already exists. Skipping.');
	} else {
	const feedTypeDefs = [
		{ name: 'Layer Feed', notes: '17% protein — for laying hens' },
		{ name: 'Scratch Grain', notes: 'Cracked corn + wheat — supplement' },
		{ name: 'Hay', notes: 'General forage — all species' },
	];

	const feedTypeIds = {};
	for (const ft of feedTypeDefs) {
		const row = await queryOne(
			`INSERT INTO feed_types (farm_id, name, notes, created_at, updated_at)
			 VALUES (:farmId, :name, :notes, :now, :now)
			 RETURNING id`,
			{ farmId, name: ft.name, notes: ft.notes, now },
		);
		feedTypeIds[ft.name] = row.id;
	}
	console.log(`Created ${feedTypeDefs.length} feed types`);

	// Helper: inserts a feed lot AND its matching financial_transactions expense row
	// in the same spirit as FeedLotService.createFeedLot.
	async function createLot({ feedTypeName, qtyPurchased, unitPrice, purchasedAt, supplier, notes }) {
		const feedTypeId = feedTypeIds[feedTypeName];
		const lot = await queryOne(
			`INSERT INTO feed_lots (farm_id, feed_type_id, qty_purchased, qty_remaining, unit_price, purchased_at, supplier, notes, created_by, created_at, updated_at)
			 VALUES (:farmId, :feedTypeId, :qty, :qty, :price, :date, :supplier, :notes, :userId, :now, :now)
			 RETURNING id`,
			{
				farmId, feedTypeId, qty: qtyPurchased, price: unitPrice,
				date: purchasedAt, supplier: supplier ?? null, notes: notes ?? null, userId, now,
			},
		);
		const amount = Number((qtyPurchased * unitPrice).toFixed(2));
		await query(
			`INSERT INTO financial_transactions (farm_id, type, amount, description, species_id, feed_lot_id, date, created_by, created_at, updated_at)
			 VALUES (:farmId, 'expense', :amount, :desc, NULL, :lotId, :date, :userId, :now, :now)`,
			{ farmId, amount, desc: `Feed purchase: ${feedTypeName}`, lotId: lot.id, date: purchasedAt, userId, now },
		);
		return lot.id;
	}

	// Two Layer Feed purchases at different prices — used to demo FIFO across lots.
	await createLot({ feedTypeName: 'Layer Feed', qtyPurchased: 30, unitPrice: 1.20, purchasedAt: '2026-01-15', supplier: 'Green Valley Feeds' });
	await createLot({ feedTypeName: 'Layer Feed', qtyPurchased: 30, unitPrice: 1.35, purchasedAt: '2026-02-20', supplier: 'Green Valley Feeds' });
	await createLot({ feedTypeName: 'Scratch Grain', qtyPurchased: 30, unitPrice: 0.80, purchasedAt: '2026-02-01', supplier: 'Local Coop' });
	await createLot({ feedTypeName: 'Hay', qtyPurchased: 200, unitPrice: 0.25, purchasedAt: '2026-01-10', supplier: 'Neighbor Farm' });
	console.log('Created 4 feed lots (with matching expense rows)');

	// Feeding schedules — active_to NULL means "until further notice".
	const scheduleDefs = [
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qtyPerDay: 7, activeFrom: '2026-01-15' },
		{ flockIdx: 0, feedTypeName: 'Scratch Grain', qtyPerDay: 1, activeFrom: '2026-02-01' },
		{ flockIdx: 1, feedTypeName: 'Layer Feed', qtyPerDay: 4, activeFrom: '2025-11-15' },
	];
	for (const s of scheduleDefs) {
		await query(
			`INSERT INTO feeding_schedules (farm_id, flock_id, feed_type_id, qty_per_day, active_from, active_to, created_at, updated_at)
			 VALUES (:farmId, :flockId, :feedTypeId, :qty, :activeFrom, NULL, :now, :now)`,
			{
				farmId, flockId: flockIds[s.flockIdx].id, feedTypeId: feedTypeIds[s.feedTypeName],
				qty: s.qtyPerDay, activeFrom: s.activeFrom, now,
			},
		);
	}
	console.log(`Created ${scheduleDefs.length} feeding schedules`);

	// Historical consumption events — drains lots via a minimal FIFO loop (same
	// ordering as drainFIFO: purchased_at ASC, id ASC). The 6 Flock A Layer Feed
	// events (7kg/day) fully drain lot 1 ($1.20) and bleed into lot 2 ($1.35),
	// producing a consumption that spans two lots with snapshotted prices —
	// exactly the FIFO shape the cost-by-flock and cost-by-lot reports surface.
	async function drainAndRecord({ flockIdx, feedTypeName, qty, consumedAt, reason }) {
		const feedTypeId = feedTypeIds[feedTypeName];
		const lots = await query(
			`SELECT id, qty_remaining, unit_price FROM feed_lots
			 WHERE farm_id = :farmId AND feed_type_id = :feedTypeId AND qty_remaining > 0
			 ORDER BY purchased_at ASC, id ASC`,
			{ farmId, feedTypeId },
		);
		let remaining = qty;
		const draws = [];
		for (const lot of lots) {
			if (remaining <= 0) break;
			const avail = Number(lot.qty_remaining);
			const draw = Math.min(avail, Number(remaining.toFixed(3)));
			if (draw <= 0) continue;
			draws.push({ lotId: lot.id, qtyDrawn: draw, unitPrice: Number(lot.unit_price) });
			remaining = Number((remaining - draw).toFixed(3));
		}
		if (remaining > 0) {
			throw new Error(`Seed: insufficient ${feedTypeName} stock for ${qty}kg on ${consumedAt}`);
		}

		const consumption = await queryOne(
			`INSERT INTO feed_consumptions (farm_id, flock_id, feed_type_id, consumed_at, qty, reason, created_by, created_at, updated_at)
			 VALUES (:farmId, :flockId, :feedTypeId, :consumedAt, :qty, :reason, :userId, :now, :now)
			 RETURNING id`,
			{
				farmId, flockId: flockIds[flockIdx].id, feedTypeId,
				consumedAt, qty, reason, userId, now,
			},
		);

		for (const d of draws) {
			await query(
				`INSERT INTO feed_consumption_lots (consumption_id, lot_id, qty_drawn, unit_price_snapshot, created_at)
				 VALUES (:cid, :lotId, :qty, :price, :now)`,
				{ cid: consumption.id, lotId: d.lotId, qty: d.qtyDrawn, price: d.unitPrice, now },
			);
			await query(
				'UPDATE feed_lots SET qty_remaining = qty_remaining - :qty, updated_at = :now WHERE id = :lotId',
				{ qty: d.qtyDrawn, lotId: d.lotId, now },
			);
		}
	}

	const consumptionDefs = [
		// Layer Flock A — six days of Layer Feed, crossing the lot boundary on day 5
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qty: 7, consumedAt: '2026-02-21', reason: 'feeding' },
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qty: 7, consumedAt: '2026-02-22', reason: 'feeding' },
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qty: 7, consumedAt: '2026-02-23', reason: 'feeding' },
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qty: 7, consumedAt: '2026-02-24', reason: 'feeding' },
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qty: 7, consumedAt: '2026-02-25', reason: 'feeding' },
		{ flockIdx: 0, feedTypeName: 'Layer Feed', qty: 7, consumedAt: '2026-02-26', reason: 'feeding' },
		// Layer Flock A — Scratch Grain
		{ flockIdx: 0, feedTypeName: 'Scratch Grain', qty: 1, consumedAt: '2026-02-22', reason: 'feeding' },
		// Dual Purpose Flock B — Layer Feed (draws from lot 2 since lot 1 is depleted by this point)
		{ flockIdx: 1, feedTypeName: 'Layer Feed', qty: 4, consumedAt: '2026-02-27', reason: 'feeding' },
	];

	for (const c of consumptionDefs) {
		await drainAndRecord(c);
	}
	console.log(`Created ${consumptionDefs.length} feed consumptions (FIFO-drained)`);
	}

	console.log('\nDev seed complete!');
	console.log('Login: testuser@test.com / Password1');
}

main()
	.catch((err) => {
		console.error('Dev seed failed:', err);
		process.exit(1);
	})
	.finally(() => sequelize.close());
