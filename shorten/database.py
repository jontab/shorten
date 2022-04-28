from datetime import datetime


from playhouse.db_url import connect
import peewee
import quart


proxy = peewee.DatabaseProxy()


class BaseModel(peewee.Model):
    """
    A base model that tells its children what database to use.
    """
    class Meta:
        database = proxy


class ShortenedLink(BaseModel):
    """
    A model that represents a shortened link.
    """
    vanity = peewee.CharField(max_length=1024, unique=True, null=True)
    original = peewee.CharField(max_length=1024)

    # The following have default values.
    created = peewee.DateTimeField(default=datetime.utcnow)
    hits = peewee.IntegerField(default=0)

    def resolve(self) -> str:
        """
        Resolves this link by prepending the base location of the site.
        """
        return quart.current_app.config["BASE_URL"] + "/" + self.vanity


class CachedFile(BaseModel):
    """
    A model that represents a file with its hash.
    """
    hash = peewee.TextField(unique=True)
    filename = peewee.TextField()
    uploaded = peewee.DateTimeField(default=datetime.utcnow)


def initialize(app: quart.Quart) -> None:
    """
    Initializes the database proxy by consulting the configuration of the
    application.
    """
    database = connect(app.config["DATABASE_URL"])
    proxy.initialize(database)

    @app.cli.command()
    def initdb() -> None:
        """
        Initializes the database by creating the necessary tables.
        """
        with proxy:
            proxy.create_tables([
                ShortenedLink,
                CachedFile,
            ])
        print("Done!")

    @app.cli.command()
    def dropdb() -> None:
        """
        Resets the database by dropping all of the tables.
        """
        with proxy:
            proxy.drop_tables([
                ShortenedLink,
                CachedFile,
            ])
        print("Done!")
