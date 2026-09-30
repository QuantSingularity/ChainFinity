# ChainFinity Contributing Guide

Thank you for considering contributing to ChainFinity! This document provides guidelines for contributing code, documentation, and tests to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. Forked and cloned the repository
2. Set up the development environment (see [Installation Guide](./INSTALLATION.md))
3. Read the [Architecture Documentation](./ARCHITECTURE.md)
4. Familiarized yourself with the codebase

### Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/abrar2030/ChainFinity.git
cd ChainFinity

# Add upstream remote
git remote add upstream https://github.com/abrar2030/ChainFinity.git

# Verify remotes
git remote -v
```

### Set Up Development Environment

```bash
# Run automated setup
./scripts/env_setup.sh --environment development

# Or manual setup
cd code/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

cd ../blockchain
npm install

cd ../web-frontend
npm install
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-new-feature
# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Convention:**

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/documentation-update` - Documentation changes
- `refactor/code-improvement` - Code refactoring
- `test/test-addition` - Test additions

### 2. Make Changes

Follow the code style guidelines below and ensure your changes:

- Are focused on a single issue or feature
- Include appropriate tests
- Update documentation as needed
- Don't break existing functionality

### 3. Test Your Changes

```bash
# Run all tests
./scripts/test_chainfinity.sh

# Run specific component tests
./scripts/test_chainfinity.sh --component backend
./scripts/test_chainfinity.sh --component blockchain
./scripts/test_chainfinity.sh --component frontend

# Check code coverage
./scripts/test_chainfinity.sh --coverage-threshold 80
```

### 4. Lint Your Code

```bash
# Run linters for all components
./scripts/lint-all.sh

# Auto-fix issues where possible
./scripts/lint-all.sh --fix
```

### 5. Commit Changes

Use conventional commit messages:

```bash
git add .
git commit -m "feat: add new risk assessment algorithm"
```

**Commit Message Format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, no logic changes)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Examples:**

```
feat(api): add portfolio export endpoint

Implement CSV and JSON export for portfolio data
with pagination and filtering support.

Closes #123
```

```
fix(contract): prevent reentrancy in withdraw function

Add ReentrancyGuard to AssetVault withdraw function
to prevent reentrancy attacks.

Fixes #456
```

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/my-new-feature

# Create pull request on GitHub
```

## Code Style Guidelines

### Python (Backend)

**Style Guide:** PEP 8 with Black formatter

**Formatting:**

```bash
# Format code with Black
black code/backend/

# Check with Flake8
flake8 code/backend/

# Type checking with mypy
mypy code/backend/
```

**Code Standards:**

1. **Imports:** Group imports (standard library, third-party, local)

   ```python
   import logging
   from datetime import datetime
   from typing import List, Optional

   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession

   from models.user import User
   from schemas.auth import LoginRequest
   ```

2. **Type Hints:** Always use type hints

   ```python
   def calculate_risk_score(
       portfolio_value: float,
       volatility: float
   ) -> float:
       return portfolio_value * volatility
   ```

3. **Docstrings:** Use Google style docstrings

   ```python
   def authenticate_user(email: str, password: str) -> Optional[User]:
       """
       Authenticate user with email and password.

       Args:
           email: User email address
           password: User password

       Returns:
           User object if authentication successful, None otherwise

       Raises:
           ValidationError: If email format is invalid
       """
       pass
   ```

4. **Async/Await:** Use async functions for I/O operations
   ```python
   async def get_user(db: AsyncSession, user_id: str) -> User:
       result = await db.execute(
           select(User).where(User.id == user_id)
       )
       return result.scalar_one_or_none()
   ```

### JavaScript/TypeScript (Frontend)

**Style Guide:** Airbnb JavaScript Style Guide

**Formatting:**

```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Auto-fix issues
npm run lint:fix
```

**Code Standards:**

1. **Use ES6+ Features:**

   ```javascript
   // Use arrow functions
   const calculateTotal = (items) =>
     items.reduce((sum, item) => sum + item.price, 0);

   // Use destructuring
   const { name, email, wallet_address } = user;

   // Use template literals
   const message = `Welcome, ${user.name}!`;
   ```

2. **React Component Style:**

   ```javascript
   // Functional components with hooks
   import React, { useState, useEffect } from "react";

   const PortfolioCard = ({ portfolio }) => {
     const [expanded, setExpanded] = useState(false);

     useEffect(() => {
       // Fetch portfolio details if expanded
       if (expanded) {
         fetchPortfolioDetails(portfolio.id);
       }
     }, [expanded, portfolio.id]);

     return (
       <Card onClick={() => setExpanded(!expanded)}>{/* Component JSX */}</Card>
     );
   };

   export default PortfolioCard;
   ```

3. **Async/Await:**
   ```javascript
   const fetchPortfolios = async () => {
     try {
       const response = await api.get("/portfolios");
       return response.data;
     } catch (error) {
       console.error("Error fetching portfolios:", error);
       throw error;
     }
   };
   ```

### Solidity (Smart Contracts)

**Style Guide:** Solidity Style Guide

**Formatting:**

```bash
# Format with Prettier
npm run format

# Lint with Solhint
npm run lint
```

**Code Standards:**

1. **Contract Structure:**

   ```solidity
   // SPDX-License-Identifier: MIT
   pragma solidity ^0.8.19;

   import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
   import "@openzeppelin/contracts/access/AccessControl.sol";

   /**
    * @title ContractName
    * @dev Contract description
    */
   contract ContractName is ReentrancyGuard, AccessControl {
     // State variables
     uint256 public totalValue;
     mapping(address => uint256) public balances;

     // Events
     event Deposit(address indexed user, uint256 amount);

     // Modifiers
     modifier onlyPositive(uint256 amount) {
       require(amount > 0, "Amount must be positive");
       _;
     }

     // Constructor
     constructor(address admin) {
       _grantRole(DEFAULT_ADMIN_ROLE, admin);
     }

     // External functions
     // Public functions
     // Internal functions
     // Private functions
   }
   ```

2. **NatSpec Comments:**

   ```solidity
   /**
    * @notice Deposits tokens into the vault
    * @dev Requires prior token approval
    * @param token Token address to deposit
    * @param amount Amount to deposit
    * @return success Whether deposit was successful
    */
   function deposit(
     address token,
     uint256 amount
   ) external nonReentrant returns (bool success) {
     // Implementation
   }
   ```

3. **Security Patterns:**
   - Always use ReentrancyGuard
   - Follow checks-effects-interactions pattern
   - Use pull over push for payments
   - Implement circuit breakers for critical functions

## Testing Requirements

### Test Coverage Requirements

| Component       | Minimum Coverage | Target Coverage |
| --------------- | ---------------- | --------------- |
| Backend         | 80%              | 85%+            |
| Smart Contracts | 85%              | 90%+            |
| Frontend        | 70%              | 80%+            |

### Backend Tests

**Test Structure:**

```python
# tests/test_auth_service.py
import pytest
from services.auth import AuthService

@pytest.mark.asyncio
async def test_authenticate_user_success(test_db):
    """Test successful user authentication"""
    auth_service = AuthService()
    user = await auth_service.authenticate_user(
        db=test_db,
        email="test@example.com",
        password="TestPass123!"
    )
    assert user is not None
    assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(test_db):
    """Test authentication with invalid password"""
    auth_service = AuthService()
    with pytest.raises(AuthenticationError):
        await auth_service.authenticate_user(
            db=test_db,
            email="test@example.com",
            password="wrongpassword"
        )
```

### Smart Contract Tests

**Test Structure:**

```javascript
// test/AssetVault.test.js
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AssetVault", function () {
  let assetVault;
  let owner, user1, user2;
  let token;

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();

    // Deploy test token
    const Token = await ethers.getContractFactory("TestToken");
    token = await Token.deploy();

    // Deploy AssetVault
    const AssetVault = await ethers.getContractFactory("AssetVault");
    assetVault = await AssetVault.deploy();
  });

  describe("deposit", function () {
    it("should allow token deposits", async function () {
      const amount = ethers.utils.parseEther("100");

      // Approve and deposit
      await token.connect(user1).approve(assetVault.address, amount);
      await expect(assetVault.connect(user1).deposit(token.address, amount))
        .to.emit(assetVault, "Deposit")
        .withArgs(user1.address, token.address, amount);

      // Check balance
      const balance = await assetVault.balanceOf(user1.address, token.address);
      expect(balance).to.equal(amount);
    });

    it("should reject zero amount deposits", async function () {
      await expect(
        assetVault.connect(user1).deposit(token.address, 0),
      ).to.be.revertedWith("Amount must be positive");
    });
  });
});
```

### Frontend Tests

**Test Structure:**

```javascript
// src/__tests__/Portfolio.test.js
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Portfolio from "../components/Portfolio";

describe("Portfolio Component", () => {
  it("renders portfolio data", async () => {
    const mockPortfolio = {
      id: "123",
      name: "Test Portfolio",
      total_value_usd: 10000,
    };

    render(<Portfolio portfolio={mockPortfolio} />);

    expect(screen.getByText("Test Portfolio")).toBeInTheDocument();
    expect(screen.getByText("$10,000.00")).toBeInTheDocument();
  });

  it("handles portfolio deletion", async () => {
    const mockOnDelete = jest.fn();
    const mockPortfolio = { id: "123", name: "Test Portfolio" };

    render(<Portfolio portfolio={mockPortfolio} onDelete={mockOnDelete} />);

    const deleteButton = screen.getByRole("button", { name: /delete/i });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockOnDelete).toHaveBeenCalledWith("123");
    });
  });
});
```

## Documentation Guidelines

### Code Documentation

1. **Document public APIs** - All public functions, classes, and endpoints
2. **Use examples** - Include usage examples in docstrings
3. **Keep it current** - Update docs when changing code
4. **Explain why** - Not just what, but why design decisions were made

### User Documentation

When adding features, update:

1. **README.md** - If it changes setup or usage
2. **API.md** - For new API endpoints
3. **CLI.md** - For new CLI commands
4. **FEATURE_MATRIX.md** - For new features
5. **examples/** - Add usage examples

### Documentation Standards

- Use Markdown format
- Include code examples with proper syntax highlighting
- Provide command examples with expected output
- Link between related documentation
- Keep table of contents updated

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally (`./scripts/test_chainfinity.sh`)
- [ ] Linting passes (`./scripts/lint-all.sh`)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with upstream main

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

Describe testing performed:

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Added tests for new features
```
