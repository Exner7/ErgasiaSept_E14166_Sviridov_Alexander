# Univeristy of Pireaus
## Department of Digital Systems
### Information Systems (September 2020 - 2021)

This project is a multi-container application for an imaginary pharmacy store named "Digital Pharmacy".

This application simulates a rudimentary e-shop that would allow the customers of the pharmacy
to search and order or purchase the pharmaceutical products that are availablel in this store.
 
The application is composed by two running docker containers.

1.  The first is a MongoDB docker container.
    This container will be providing the database system for this application.
    The database itself is called "DSPharmacy" and will be containing two collections:

    -   Users: this collection stores all of the records of the system's users
    -   Products: this collection stores all the records of the available products

2.  The second docker container will be running the web-service itself.
    This web-service is implemented as a flask application.
    The web-service provides the following endpoints to the different types of users of the system:

    Guest
    --
    -   `[POST]`      `/signup`

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "ssn": <int>, /* formatted as DDMMYYNNNNN (11-digits) integer*/
            "name": <string>,
            "email": <string>,
            "password": <string>,
        }
        ```
        (*ssn*  must be formatted as DDMMYYNNNNN where DD the day of birth,
        MM the month of birth, YY is the two last digits of the year of birth, and
        NNNNN is a random number.)

        Inserts a new user document into the **Users** collection of the ***DSPharmacy*** database.

        ![](screenshots/signup-before.jpg)
        ![](screenshots/signup.jpg)
        ![](screenshots/signup-after.jpg)

    -   `[POST]`      `/login`

        **Expects** JSON Data in the Body of the Request, in the following format:

        *For an administrator Log-In*
        
        ```json
        {
            "username": <string>,
            "password": <string>,
        }
        ```

        ![](screenshots/login-as-admin.jpg)

        *For a user Log-In:*

        ```json
        {
            "email": <string>,
            "password": <string>,
        }
        ```

        ![](screenshots/login-as-user.jpg)

        Creates a new *administrator* or *user* session respectively,
        and returns a response containing an *Authorization Key*.

        This *Authorization Key* is to be used for each subsequent request.
    
    Administrator or User
    --

    -   `[POST]`      `/product-search`

        ***client must be authenticated as an administrator or a user***

        ![](screenshots/login-as-user.jpg)

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        ![](screenshots/product-search-authorization.jpg)

        **Expects** JSON Data in the Body of the Request, in the following format:


        -   *to perform search for a product by ID*
            ```json
            {
                "_id": <string>
            }
            ```
            ![](screenshots/product-search-id.jpg)
        -   *to perform search producta by name*
            ```json
            {
                "name": <string>
            }
            ```
            ![](screenshots/product-search-name.jpg)
        -   *to perform search for a product by category*
            ```json
            {
                "category": <string>
            }
            ```
            ![](screenshots/product-search-category.jpg)
        
        Returns the products from the **Products** collection of the ***DSPharmacy*** database,
        that are matching the search term(s) provided in the JSON Data in the Body of the Request.

    Administrator
    --

    -   `[POST]`      `/admin/create-product`

        ***client must be authenticated as an administrator***

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "name": <string>,
            "category": <string>,
            "description": <string>,
            "price": <float>,
            "stock": <int>
        }
        ```

        Inserts a new product document
        into the **Products** collection of the ***DSPharmacy*** database.

        ![](screenshots/create-product-before.jpg)
        ![](screenshots/login-as-admin.jpg)
        ![](screenshots/create-product-authorization.jpg)
        ![](screenshots/create-product.jpg)
        ![](screenshots/create-product-after.jpg)
    
    -   `[PUT]`      `/admin/update-product`

        ***client must be authenticated as an administrator***

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "_id": <string>, /* REQUIRED */

            /* Any subset of the below key-value pairs is sufficient to make the request*/
            "name": <string>,
            "category": <string>,
            "description": <string>,
            "price": <float>,
            "stock": <int>
        }
        ```
        (Besides the *_id*, only a subset of the key-value pairs is mandatory)

        Finds a product document in the **Products** collection of the ***DSPharmacy*** database,
        using the *_id* provided in the JSON Data in the Body of the Request, and
        updates the matching product document using the rest of the key-value pairs
        provided in the JSON Data in the Body of the Request.

        ![](screenshots/create-product-after.jpg)
        ![](screenshots/login-as-admin.jpg)
        ![](screenshots/update-product-authorization.jpg)
        ![](screenshots/update-product.jpg)
        ![](screenshots/update-product-after.jpg)

    -   `[DELETE]`    `/admin/delete-product`

        ***client must be authenticated as an administrator***

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "_id": <string>
        }
        ```

        Finds a product document in the **Products** collection of the ***DSPharmacy*** database,
        using the *_id* provided in the JSON Data in the Body of the Request, and
        deletes the matching product document
        from the **Products** collection of the ***DSPharmacy*** database

        ![](screenshots/delete-product-before.jpg)
        ![](screenshots/login-as-admin.jpg)
        ![](screenshots/delete-product-authorization.jpg)
        ![](screenshots/delete-product.jpg)
        ![](screenshots/delete-product-after.jpg)
    
    User
    --

    -   `[POST]`      `/user/add-to-cart`

        ***client must be authenticated as a user***
        ![](screenshots/login-as-user.jpg)
        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        ![](screenshots/add-to-cart-authorization.jpg)

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "_id": <string>,
            "quantity": <int>
        }
        ```
        ![](screenshots/add-to-cart.jpg)
        Finds a product document in the **Products** collection of the ***DSPharmacy*** database,
        using the *_id* provided in the JSON Data in the Body of the Request, and
        inserts the matching product document into the user's cart if the stock is sufficient.

        There are three product categories which are not available for underage users.
        
        -   analgesic
        -   antibiotic
        -   antiseptic

        If the specified product is within one of these categories and the user is under 18 years old,
        then the product cannot be added to the cart.

    -   `[POST]`      `/user/view-cart`

        ***client must be authenticated as a user***
        
        ![](screenshots/login-as-user.jpg)
        
        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`
        
        ![](screenshots/view-cart-authorization.jpg)

        Returns the current cart of the user.
        
        ![](screenshots/view-cart.jpg)

    -   `[DELETE]`    `/user/remove-from-cart`

        ***client must be authenticated as a user***

        ![](screenshots/login-as-user-2.jpg)

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        ![](screenshots/remove-from-cart-authorization.jpg)

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "_id": <string>
        }
        ```

        ![](screenshots/remove-from-cart.jpg)

        Removes specified by *_id* (provided within the JSON Data in the Body of the Request)
        product from user's cart.
    
    -   `[POST]`      `/user/checkout`

        ![](screenshots/checkout-before.jpg)

        ***client must be authenticated as a user***

        ![](screenshots/login-as-user-2.jpg)

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        ![](screenshots/checkout-authorization.jpg)

        **Expects** JSON Data in the Body of the Request, in the following format:

        ```json
        {
            "credit": <string> /* 16-digit numeric string */
        }
        ```
        ![](screenshots/checkout.jpg)

        Simulates a checkout process.
        Validates credit-card-number (*credit*)
        Constructs a receipt representation.
        Updates stock of the purchased products.
        If the stock for a product in the cart is not sufficient, then it is skipped.
        Which means that it is not purchased and remains in the cart.
        Adds the receipt representation to the users's order history.
        Returns the receipt representation.

        ![](screenshots/checkout-after.jpg)
    
    -   `[POST]`      `/user/view-order-history`

        ***client must be authenticated as a user***

        ![](screenshots/login-as-user-2.jpg)

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        ![](screenshots/view-order-history.jpg)

        Returns the order history of the user.
    
    -   `[DELETE]`    `/user/delete-account`

        ***client must be authenticated as a user***

        **Expects** The *Authorization Key* in the Header of the Request as returned by `/login`

        ![](screenshots/delete-account.jpg)

        Deletes user's session and user's account from the System.

        ![](screenshots/delete-account-after.jpg)
