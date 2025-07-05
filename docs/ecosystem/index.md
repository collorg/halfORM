# halfORM Ecosystem

!!! note "Work in Progress"
    The halfORM ecosystem is actively evolving. This documentation outlines our vision and current development efforts. **We welcome contributions, feedback, and ideas from the community!**
    
    - 💬 **Share your thoughts**: [GitHub Discussions](https://github.com/collorg/halfORM/discussions)
    - 🐛 **Report issues**: [GitHub Issues](https://github.com/collorg/halfORM/issues)
    - 🤝 **Contribute**: Help shape the future of halfORM development tools

The halfORM ecosystem extends the core PostgreSQL-native ORM with a rich set of tools and extensions for modern development workflows. Built on a **database-first philosophy**, the ecosystem provides everything from development frameworks to production-ready APIs.

## Architecture Overview

The halfORM ecosystem is designed around three complementary layers:

### **🧩 Extensions Layer** 
*Optional and modular*
- `half-orm-litestar-api` - REST API generation
- `half-orm-admin` - Admin interfaces  
- `half-orm-monitoring` - Observability tools
- *...and more community extensions*

**↕️ Extends**

### **🛠️ halfORM_dev Layer**
*Development Framework & hop command*
- Project management and scaffolding
- Database patch system with versioning
- Code generation and Git integration  
- **Extension point** for ecosystem tools

**↕️ Built on**

### **🗃️ halfORM Core Layer**
*PostgreSQL-native ORM - Stable and independent*
- Database introspection and relation classes
- Query building with transparent SQL
- Transaction management
- **Can be used standalone**

## Core Components

### 🗃️ halfORM Core
**Status**: Stable and mature  
**Purpose**: PostgreSQL-native Object-Relational Mapper

The foundation layer that can be used independently. Provides:
- Database introspection and relation classes
- Query building with transparent SQL generation
- Transaction management
- Advanced PostgreSQL feature support

```python
from half_orm.model import Model

# Direct usage - no framework required
blog = Model('blog_db')
Post = blog.get_relation_class('blog.post')

# Immediate productivity
for post in Post(is_published=True).ho_order_by('created_at DESC'):
    print(post['title'])
```

**[📖 Learn halfORM Core →](../index.md)**

### 🛠️ halfORM_dev
**Status**: Early Alpha - Breaking changes expected  
**Purpose**: Development framework with project management capabilities

Vision for comprehensive development capabilities:
- Project scaffolding and structure
- Database patch management with semantic versioning
- Automatic code generation synchronized with schema
- Git workflow integration
- Testing framework
- Production deployment tools

```bash
# Planned development lifecycle
pip install half-orm-dev
hop new my_project --devel
hop prepare -l minor -m "Add user system"
hop apply
hop release
```

**[📖 Learn about halfORM_dev →](half-orm-dev.md)**

### 🧩 Extensions
**Status**: Concept phase - Proof of concepts in development  
**Purpose**: Specialized tools that will extend halfORM_dev

Planned packages that will integrate with the `hop` command:

| Extension | Purpose | Status | Planned Commands |
|-----------|---------|--------|----------|
| **[half-orm-litestar-api](extensions/litestar-api.md)** | REST API generation | 🧪 Proof of Concept | `hop litestar-api generate` |
| **[half-orm-admin](extensions/admin.md)** | Admin interface | 💭 Concept | `hop admin setup` |
| **[half-orm-monitoring](extensions/monitoring.md)** | Observability tools | 💭 Concept | `hop monitoring dashboard` |

## Getting Started

### Quick Start Path

```bash
# 1. Choose your approach
pip install half-orm          # Core only - integrate into existing project
# OR
pip install half-orm-dev      # Full development framework

# 2. If using halfORM_dev, create project
hop new my_project --devel
cd my_project

# 3. Add extensions as needed
pip install half-orm-litestar-api
hop litestar-api init

# 4. Enhanced workflow
hop prepare -l patch
hop apply
hop litestar-api generate
hop release
```

### Learning Path

**🚀 New to halfORM?**
1. Start with [halfORM Quick Start](../quick-start.md)
2. Learn [core concepts](../fundamentals.md)
3. Try the [tutorial](../tutorial/index.md)

**🔥 Interested in development frameworks?**
1. Learn about [halfORM_dev vision](half-orm-dev.md)
2. Review the [guidelines](guidelines.md)
3. Consider [contributing](development/getting-started.md)

**⚡ Want to contribute or follow development?**
Follow progress on the [extension development](extensions/index.md)

## Use Cases

### 🎯 Core halfORM Only
Perfect for:
- **Existing applications** - Add powerful PostgreSQL ORM
- **Microservices** - Lightweight database layer  
- **Data analysis** - Explore and manipulate data
- **Custom integrations** - Build your own tooling

```python
# Clean, direct database access
from half_orm.model import Model

analytics = Model('analytics_db')
Events = analytics.get_relation_class('public.events')

# Powerful querying without framework overhead
daily_stats = (Events(date=('>', '2024-01-01'))
               .ho_order_by('date')
               .ho_select('date', 'count', 'revenue'))
```

### 🛠️ halfORM_dev Framework
Vision for:
- **New applications** - Complete development lifecycle
- **Team projects** - Standardized workflow and structure
- **Database evolution** - Managed schema changes
- **Production deployments** - Automated patch system

```bash
# Envisioned development workflow
hop new company_app --devel
hop prepare -l minor -m "Add payment system"
# ... develop and test ...
hop release --push
```

### 🧩 Extended Ecosystem
Vision for:
- **API-first applications** - Automatic REST/GraphQL generation
- **Admin panels** - Ready-made management interfaces
- **Monitoring** - Built-in observability
- **Custom workflows** - Extensible framework

```bash
# Envisioned rich development experience
pip install half-orm-litestar-api half-orm-admin
hop litestar-api generate --openapi
hop admin setup --auth
```

## Why halfORM Ecosystem?

### Database-First Philosophy

Unlike code-first ORMs, halfORM puts your PostgreSQL database at the center:

✅ **Schema in SQL** - Use PostgreSQL's full power  
✅ **No migrations** - Schema changes happen in SQL  
✅ **Instant integration** - Works with existing databases  
✅ **SQL transparency** - See exactly what queries run  

### Modular Architecture

Choose exactly what you need:

✅ **Core only** - Lightweight ORM for specific use cases  
✅ **Development framework** - Complete project management  
✅ **Extensions** - Add functionality incrementally  
✅ **Custom extensions** - Build your own tools  

### Production Ready

Built for real applications:

✅ **Mature core** - Stable API, extensive testing  
✅ **Patch system** - Safe database evolution  
✅ **Git integration** - Professional development workflow  
✅ **Deployment tools** - Production-tested processes  

## Extension Development

### For Extension Developers

The halfORM ecosystem welcomes contributions! Building extensions is straightforward:

```python
# half_orm_myextension/hop_extension.py
def add_commands(hop_main_group):
    @hop_main_group.group()
    def myfeature():
        """My custom functionality"""
        pass
    
    @myfeature.command()
    def generate():
        """Generate my custom output"""
        # Your extension logic here
        pass
```

**[📖 Extension Development Guide →](development/getting-started.md)**

### Standards and Guidelines

- **[Development Guidelines](guidelines.md)** - Standards for the ecosystem
- **[Plugin API](development/plugin-api.md)** - Technical integration reference
- **[Best Practices](development/best-practices.md)** - Proven patterns
- **[Publishing Guide](development/publishing.md)** - Share your extension

## Community and Support

### Get Involved

- **[GitHub Discussions](https://github.com/collorg/halfORM/discussions)** - Ask questions, share ideas
- **[Issues](https://github.com/collorg/halfORM/issues)** - Report bugs, request features
- **[Contributing](guidelines.md#contribution-process)** - Help build the ecosystem

### Resources

- **[Extension Registry](extensions/index.md)** - Browse available extensions
- **[Examples Repository](../examples/index.md)** - Real-world usage patterns
- **[API Reference](../api/index.md)** - Complete technical documentation

## Roadmap and Vision

### Current Reality
- ✅ halfORM Core - Stable production release
- 🧪 halfORM_dev - Early alpha with breaking changes expected
- 🧪 half-orm-litestar-api - Proof of concept stage
- 📋 Extension ecosystem - Guidelines and architecture planning

### Development Focus
- 🎯 Stabilizing halfORM_dev architecture
- 🎯 Plugin system implementation
- 🎯 Extension development standards
- 🎯 Community feedback and iteration

### Future Vision
- 🚀 Mature development framework
- 🚀 Rich ecosystem of community extensions
- 🚀 Enterprise-grade tooling
- 🚀 Advanced integrations and workflows

*Note: This ecosystem represents our vision for the future of halfORM development tools. Current implementations are experimental and subject to significant changes.*

## Getting Help

### Documentation Paths
- **New users**: [Quick Start](../quick-start.md) → [Tutorial](../tutorial/index.md)
- **Developers**: [halfORM_dev](half-orm-dev.md) → [Guidelines](guidelines.md)
- **Contributors**: [Development Guide](development/getting-started.md)

### Support Channels
- **Questions**: [GitHub Discussions](https://github.com/collorg/halfORM/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/collorg/halfORM/issues)
- **Feature requests**: [Discussions](https://github.com/collorg/halfORM/discussions/categories/ideas)

---

**The halfORM ecosystem brings the power of PostgreSQL to modern Python development with tools that respect your database design and enhance your development workflow.**

Ready to get started? **[Install halfORM →](../quick-start.md)** or **[Explore the halfORM_dev vision →](half-orm-dev.md)**