# Validate Breed-Species Match on Animal Creation

**User Story:**  
As a user,  
I want to be prevented from assigning a breed to an animal if it does not belong to the selected species,  
so that my animal records are always accurate and consistent.

**Acceptance Criteria:**

-   Animal creation fails with a clear error if `breedId` does not match the provided `speciesId`.
-   Error message is user-friendly and actionable.
-   API documentation (Bruno) is updated to reflect this validation.
-   Unit and integration tests cover this scenario.

**Status:** To Do
