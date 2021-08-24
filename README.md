
# Auth Simple for Streamlit
> _A simple username/password database authentication solution for Streamlit_

> Arvindra Sehmi, CloudOpti Ltd. | [Website](https://sehmiconscious.blogspot.com) | [LinkedIn](https://www.linkedin.com/in/asehmi/)

> Updated: 24 August, 2021

---

I liked the simplicity of the username/password database authentication solution in [this post](https://discuss.streamlit.io/t/authentication-script/14111) (by [madflier](https://discuss.streamlit.io/u/madflier)) over in the [Streamlit discussion forum](https://discuss.streamlit.io/). I thought I'd have a go at making it more _flexible_ and possibly _production ready_. My thought is contrary to madflier's objectives around simplicity, but since I've seen a lot of requests for simple database-backed authentication in the Streamlit discussion forum I felt it was worth the effort to take his solution one step further. I'm honoured to be a member of Streamlit's [Creators](https://streamlit.io/creators) group and I the opportunity to work on my ideas in a recent Streamlit internal hackathon. Apologies to madflier! :-)

As a side note, I've already implemented a [Streamlit component for Auth0 Authentication](https://github.com/asehmi/Data-Science-Meetup-Oxford/tree/master/StreamlitComponent). That's definitely the way to go, but feel that the Streamlit community has been a little hesitant to take it up. Perhaps it's considered to be something for use in _big enterprise_ applications? That's not my experience, given how easy it is to use [Auth0](https://auth0.com). Streamlit components can get complicated and require separate Streamlit and web apps to make them work. So, perhaps something with fewer moving parts is more palatable for most folks (a) getting started with Streamlit, **and** (b) needing authentication to boot?

I've redesigned the solution with the following features:

- Added session state support so logins survive a Streamlit's top-down reruns which occur in it's normal execution.
- Added support for `logout`, `authenticated` check, and a `requires_auth` function decorator to protect areas of your own apps, e.g. secure pages in a multi-page Streamlit application.
- Built-in authentication/login status header widget that will sit nicely in most Streamlit apps.
- Refactored the SQLite local DB dependency in the main auth module so it uses a DB provider design pattern implementation.
- Given the refactoring, I added a simple factory for multiple provider implementations, so different persistence technologies could be used, for example a cloud DB.
  - In fact, I built an Airtable cloud databse provider which can replace SQLite as an alternative.
- The abstract provider interface is super simple and should allow _almost_ any database to be adapted, and it works fine for this specific auth use case in the implementations I created.
- Configuration has been externalised for things like database names and locations, cloud service account secrets, api keys, etc. The configuration is managed in a root `.env` and `env.py` files, and small Python settings files for the main app (`app_settings.py`), and each provider implementation (`settings.py`).
- There's just enough exception handling to allow you to get a handle on your own extension implementations.
- I use `debugpy` for remote debugging support of Streamlit apps, and include a litte module that makes it work better with Streamlit's execution reruns.

All code is published under [MIT license](./LICENSE), so feel free to make changes and please **fork the repo if you're making changes and submit pull requests**.

If you like this work, consider clicking that **star** button. Thanks!

## Demos

### Test application

The Streamlit app `app.py` illustrates how to hook `authlib` into your Streamlit applications.

![app.py](./auth-simple-demo.gif)

### Database Admin

The Streamlit app `admin.py` illustrates how to auto-start `authlib`'s superuser mode to create an initial SQLite database and manage users and user credentials.

![admin.py](./auth-simple-admin-demo.gif)

## Installation and running the app

To install the pre-requisites, open a console window in the root folder and run:

```bash
$ pip install -r requirements.txt
```

To run the sample application, open a console window in the root folder and run:

```bash
# Starts the app on the default port 8765
$ streamlit run app.py

# I use a specific port 8080 like this
$ streamlit run --server.port 8080 app.py
```

To run the DB Admin application, open a console window in the root folder and run:

```bash
$ streamlit run admin.py
```

## Getting started with a SQLite database

There's nothing you need to do as SQLite is part of Python (I use version 3.8.10). The `admin.py` Streamlit application will handle creating a database and `users` table for you, and then allow you to populate users, and edit existing databases.

1. First, assign the `STORAGE` value in the `.env` file in the application root folder.

For example:

**.env** file

```bash
# Options are 'SQLITE', 'AIRTABLE'
STORAGE='SQLITE'
```

A full example (which includes Airtable settings) is available in `env.sample`.

2. Then, you must run the admin app as shown above to create your initial SQLite database!

## Getting started with an Airtable database

### How to create an Airtable

1. First, login into or create a (free) [**Airtable account**](https://airtable.com/account).
2. Next, follow these steps to create an Airtable:

- Create a database (referred to as a _base_ in Airtable) and a table within the base.
- You can call the base `profile` and the table `users`
- Rename the primary key default table field (aka column) to `username` (field type 'Single line text')
- Add a `password` field (field type 'Single line text')
- Add a `su` (superuser) field (field type 'Number')

### Finding your Airtable settings

1. You can initially create and then manage your API key in the 'Account' overview area
2. For your base (e.g. `profile`) go to the 'Help menu' and select 'API documentation'
3. In 'API documentation' select 'METADATA'
4. Check 'show API key' in the code examples panel, and you will see something like this:

```bash
EXAMPLE USING QUERY PARAMETER
$ curl https://api.airtable.com/v0/appv------X-----c/users?api_key=keyc------X-----i
```

- `keyc------X-----i` is your 'API_KEY' (also in your 'Account' area)
- `appv------X-----c` is your 'BASE_ID',
- `users` will be your 'TABLE_NAME'

### Configuring Airtable's app settings 

Assign these values to the keys in the Airtable section of the `.env` file in the application root folder.

For example:

**.env** file

```bash
# Options are 'SQLITE', 'AIRTABLE'
STORAGE='AIRTABLE'

# Airtable account
AIRTABLE_API_KEY='keyc------X-----i'
AIRTABLE_PROFILE_BASE_ID = 'appv------X-----c'
USERS_TABLE = 'users'
```

A full example (which includes SQLite settings) is available in `env.sample`.

That's it! You're ready now to use the admin application or Airtable directly to manage the credentials of your users.

## TODO

Caveat emptor: you're free to use this solution at your own risk. I have a few more things to do:

- Store a hashed password in the database, not as plain text. Note, the password is never sent to the browser - it's retrieved and matched on the Streamlit server - so is quite secure, but I'm definitely not following OWASP best practice.
- Fix column and sort order in user table view from Airtable
- In addition to *username*, *password*, and *su* I want to add additional useful user data to the database: *logged_in*, *expires_at*, *logins_count*, *last_login*, *created_at*, *updated_at*.
- Provide a Streamlit component wrapper to make it easy to _pip install_ and also use this simple authentication within custom component implementations.
- Deploy the demo app on [Streamlit sharing](https://share.streamlit.io/) and use it's secrets store instead of my `.env` solution.