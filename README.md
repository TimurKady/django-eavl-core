> ⚠️ This project is in an early experimental stage.  
> It is under active development and may change at any time.  
> Nothing is guaranteed to work as expected — use at your own risk.


# Django Datacore
EAVL data model for Django

# Introduction to EAVL

EAVL (Entity-Attribute-Value-Link) is a data organization methodology that allows for flexible and efficient management of diverse types of information. The fundamental idea behind EAVL is to create a data structure capable of storing various attributes for entities in a system without the need to define them all in advance.

## Key Concepts of EAVL

1. **Entities**: In EAVL, data is organized around entities. Entities can be anything from products and customers to events and orders. Each entity has a unique identifier.

2. **Attributes**: Attributes are the characteristics or properties of entities. They can be numerical, textual, date-related, and more. It's important to note that EAVL allows for the addition of new attributes for entities at any time without altering the database schema.

3. **Values**: Values are specific data associated with attributes for a particular entity. They can vary for different entities.

4. **Links**: Links are an additional aspect of EAVL that allows for establishing relationships between entities. These links can represent various types of relationships, such as ownership, dependency, or ownership. Links enable the creation of more complex data structures that reflect real-world connections between entities.

## Advantages of EAVL

- **Flexibility**: EAVL enables the adaptation of data structures to changing requirements without the need for a complete database overhaul.

- **Diverse Attributes**: You can store virtually unlimited attributes for each entity, which is particularly useful when dealing with heterogeneous data.

- **Efficiency**: EAVL can be an efficient way to store data when queries are properly designed.

## Quick Start: django-eavl-core

The project can use the [django-eavl-core](https://github.com/TimurKady/django-eavl-core)
package to store entities with flexible attributes.

1. Install the package (if it is not already included):

   ```bash
   pip install git+https://github.com/TimurKady/django-eavl-core.git
   ```

2. Register the app in `config/settings/base.py`:

   ```python
   INSTALLED_APPS = [
       ...,
       'datacore',
   ]
   ```

3. Define your entity classes by subclassing `AbstractEntityClassModel`:

   ```python
   # apps/cars/models.py
   from datacore.models import AbstractEntityClassModel

   class Car(AbstractEntityClassModel):
       class Meta:
           verbose_name = 'car'
           verbose_name_plural = 'cars'
   ```

   When this class is imported, `django-eavl-core` automatically generates
   models for the car entity, its attributes and values.

4. Make and apply migrations:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Use the API to work with entities:

   ```python
   from apps.cars.models import Car

   car = Car.objects.create(title='Model X')
   car.set_data(color='red', mileage=5000)
   print(car.get_data())  # {'color': 'red', 'mileage': 5000}
   ```



## Limitations of EAVL

- **Query Complexity**: Retrieving data from the EAVL structure may require more complex queries and can complicate the data analysis process.

- **Integration**: Integrating data from EAVL with other systems can be a more challenging task.

This package implements the EAVL model for Django. During its implementation, special attention was paid to performance issues for high-load systems and overcoming the limitations mentioned above.
