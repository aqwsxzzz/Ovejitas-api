# Validate Parent Sex and Rename Field for Animal Creation

**User Story:**  
As a user,  
I want to ensure that when creating an animal, the selected parent's sex matches the parental role (i.e., only males can be assigned as father, only females as mother),  
so that animal lineage data remains accurate and logical.

**Acceptance Criteria:**

-   Animal creation fails with a clear, user-friendly error if the selected father is not male or the selected mother is not female.
-   The database field currently named `parentId` is renamed to `fatherId` to match the existing `motherId` field and clarify intent.
-   All relevant code, models, migrations, and documentation are updated to reflect this change.
-   API documentation (Bruno) is updated to reflect this validation and field renaming.
-   Unit and integration tests cover these scenarios.

**Status:** Done
