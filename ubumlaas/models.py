import variables as v
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import and_, or_, text, desc, asc

from flask_login import UserMixin,AnonymousUserMixin


@v.login_manager.user_loader
def load_user(user_id):
    """Get user by id.

    Arguments:
        user_id {int} -- user identificator.

    Returns:
        User -- User with that id.
    """
    v.app.logger.info("Getting user with id %s from the data base", user_id)
    us= User.query.get(user_id)
    if us is None:
        return AnonymousUserMixin()
    else:
        return us


def load_experiment(exp_id):
    """Get experiment by id.

    Arguments:
        exp_id {int} -- experiment identificator.

    Returns:
        Experiment -- Experiment with that id.
    """
    v.app.logger.info("Getting experiment with id %s from the data base", exp_id)
    return Experiment.query.get(exp_id)


def get_experiments(idu):
    """Get all experiments from an user.

    Arguments:
        idu {int} -- user identificator.

    Returns:
        experiments list -- all experiments from user with that id.
    """
    listexp_db = Experiment.query.filter(Experiment.idu == idu).all()
    listexp = []
    for i in listexp_db:
        d = i.to_dict()
        d['starttime'] = datetime.fromtimestamp(i.starttime)\
            .strftime("%d/%m/%Y - %H:%M:%S")
        if i.endtime is not None:
            d['endtime'] = datetime.fromtimestamp(i.endtime)\
                .strftime("%d/%m/%Y - %H:%M:%S")
        else:
            d['endtime'] = None
        d['web_name'] = i.web_name()
        d['state'] = i.state
        listexp.append(d)
    v.app.logger.info("Getting experiments from user with id %d, %d experiments found", idu, len(listexp))
    return listexp


def get_algorithms_type():
    sql = text('SELECT DISTINCT alg_typ FROM algorithms')
    result = v.db.engine.execute(sql)
    types = [(row[0], row[0]) for row in result if row[0] != "Mixed"]
    v.app.logger.info("Getting algorithm types")
    return types


def get_similar_algorithms(alg_name, exp_typ):
    v.app.logger.info("Getting algorithm similar to %s", alg_name)
    alg = get_algorithm_by_name(alg_name)
    if alg.lib == "meka":
        cond = and_(Algorithm.lib == "weka",
                    or_(Algorithm.alg_typ == "Classification",
                        Algorithm.alg_typ == "Mixed"))
    else:
        cond = Algorithm.lib == alg.lib
        subcond = Algorithm.alg_typ == exp_typ
        if exp_typ in ["Classification", "Regression", "Semi Supervised Classification"]:
            subcond = or_(subcond, Algorithm.alg_typ == "Mixed")
        cond = and_(cond, subcond)
    algorithms = Algorithm.query.filter(cond).all()
    return algorithms


def get_algorithms(alg_typ):
    """Get algorithms by type.

    Arguments:
        alg_typ {string} -- algorithm type.

    Returns:
        algorithm list -- all algorithm of that type.
    """
    v.app.logger.info("Getting all %s algorithms", alg_typ)
    cond = Algorithm.alg_typ == alg_typ
    if alg_typ in ["Classification", "Regression"]:
        cond = or_(cond, Algorithm.alg_typ == "Mixed")
    return Algorithm.query.filter(cond).order_by(asc(Algorithm.web_name)).all()


def get_algorithm_by_name(name):
    """Get an algorithm by name.

    Arguments:
        name {string} -- name of the algorithm.

    Returns:
        Algorithm -- Algorithm with that name.
    """
    v.app.logger.info("Getting algorithm %s by name", name)
    return Algorithm.query\
        .filter(Algorithm.alg_name == name).first()


def get_filter_by_name(name):
    """Get an filter by name.

    Arguments:
        name {string} -- name of the filter.

    Returns:
        Filter -- Filter with that name.
    """
    v.app.logger.info("Getting filter %s by name", name)
    return Filter.query\
        .filter(Filter.filter_name == name).first()


def get_compatible_filters(lib, typ=None, alg_typ=None):
    """Get an filter by .

    Arguments:
        lib {string} -- name of the library sklearn, weka or is_ssl.
        alg_typ {string} -- algorithm type Classification, Regression, etc.

    Returns:
        Algorithm -- Algorithm with that name.
    """
    cond = Filter.lib == lib
    if typ is not None:
        cond = and_(cond, Filter.typ == typ)
    if alg_typ in ['Classification', 'Semi Supervised Classification', 'Mixed']:
        filters = []
        if lib != 'is_ssl':
            cond1 = Filter.lib == 'is_ssl'
            filters = Filter.query.filter(cond1).all()
            v.app.logger.info("Getting filter for is_ssl")
        [filters.append(x) for x in Filter.query.filter(cond).all()]
        return filters
    v.app.logger.info("Getting filter for %s", lib)
    return Filter.query\
        .filter(cond).all()

def delete_experiment(id):
    v.app.logger.info("Deleting experiment with id %d", int(id))
    Experiment.query.filter_by(id=id).delete()
    v.db.session.commit()

class User(v.db.Model, UserMixin):

    __tablename__ = 'users'

    id = v.db.Column(v.db.Integer, primary_key=True)
    email = v.db.Column(v.db.String(64), unique=True, index=True)
    username = v.db.Column(v.db.String(64), unique=True, index=True)
    password_hash = v.db.Column(v.db.String(128))
    activated = v.db.Column(v.db.Boolean, nullable=False, default=False)
    desired_use = v.db.Column(v.db.String(64))
    country = v.db.Column(v.db.String(64))
    user_type = v.db.Column(v.db.Integer, nullable=False, default=1)
    website = v.db.Column(v.db.String(128))
    twitter = v.db.Column(v.db.String(64))
    github = v.db.Column(v.db.String(64))
    institution = v.db.Column(v.db.String(128))
    linkedin = v.db.Column(v.db.String(64))
    google_scholar = v.db.Column(v.db.String(64))

    def __init__(self, email, username, password, desired_use, country, activated, user_type):
        """User constructor

        Arguments:
            email {string} -- User's email
            username {string} -- User name identifer
            password {string} -- User's password
            desired_use {string} -- User's intended use
            country {string} -- User's country
        """
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.desired_use = desired_use
        self.country = country
        self.activated = activated
        self.user_type = user_type
        self.website = None
        self.twitter = None
        self.github = None
        self.institution = None
        self.linkedin = None
        self.google_scholar = None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Compare input password with current password

        Arguments:
            password {string} -- Input password

        Returns:
            boolean -- True if both password match, instead False
        """
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return True if self.user_type == 0 else False

    def __repr__(self):
        """Representation

        Returns:
            str -- representation
        """
        return f"Email: {self.email} Username: {self.username}"

    def __str__(self):
        """to string

        Returns:
            str -- information string
        """
        return self.__repr__() + f" Email: {self.email}"

    def to_dict(self):
        """Object to dict

        Returns:
            dict -- dict with key and value from the object.
        """
        return {"id": self.id,
                "email": self.email,
                "username": self.username,
                "password": self.password_hash
                }
    
    def to_dict_all(self):
        """Object to dict

        Returns:
            dict -- dict with all atributes except password.
        """
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "desired_use": self.desired_use,
            "country": self.country,
            "activated": self.activated,
            "user_type": self.user_type,
            "website": self.website,
            "twitter": self.twitter,
            "github": self.github,
            "institution": self.institution,
            "linkedin": self.linkedin,
            "google_scholar": self.google_scholar
        }


class Algorithm(v.db.Model):

    __tablename__ = 'algorithms'

    id = v.db.Column(v.db.Integer, primary_key=True)
    alg_name = v.db.Column(v.db.String(64), unique=True)
    web_name = v.db.Column(v.db.String(64))
    alg_typ = v.db.Column(v.db.String(64))
    config = v.db.Column(v.db.Text)
    lib = v.db.Column(v.db.String(64))

    def __init__(self, alg_name, web_name, alg_typ, config, lib):
        """Algorithm constructor.

        Arguments:
            alg_name {str} -- algorithm name.
            web_name {str} -- algorithm web name.
            alg_typ {str} -- algorithm type
            config {str} -- json with algorithm configuration.
            lib {str} -- sklearn or weka.
        """

        self.alg_name = alg_name
        self.web_name = web_name
        self.alg_typ = alg_typ
        self.config = config
        self.lib = lib

    def to_dict(self):
        """Algorithm to dict

        Returns:
            dict -- dict with keys and values from Algorithm Object.
        """
        return {"id": self.id,
                "alg_name": self.alg_name,
                "web_name": self.web_name,
                "alg_typ": self.alg_typ,
                "config": self.config,
                "lib": self.lib}


class Filter(v.db.Model):

    __tablename__ = "filters"

    id = v.db.Column(v.db.Integer, primary_key=True)
    filter_name = v.db.Column(v.db.String(64), unique=True)
    web_name = v.db.Column(v.db.String(64))
    filter_typ = v.db.Column(v.db.String(64))
    config = v.db.Column(v.db.Text)
    lib = v.db.Column(v.db.String(64))

    def __init__(self, filter_name, web_name, filter_typ, config, lib):
        """Algorithm constructor.

        Arguments:
            filter_name {str} -- filter name.
            web_name {str} -- filter web name.
            filter_typ {str} -- filter type
            config {str} -- json with filter configuration.
            lib {str} -- sklearn, weka or is_ssl.
        """

        self.filter_name = filter_name
        self.web_name = web_name
        self.filter_typ = filter_typ
        self.config = config
        self.lib = lib

    def to_dict(self):
        """Algorithm to dict

        Returns:
            dict -- dict with keys and values from Filter Object.
        """
        return {"id": self.id,
                "filter_name": self.filter_name,
                "web_name": self.web_name,
                "filter_typ": self.filter_typ,
                "config": self.config,
                "lib": self.lib}


class Experiment(v.db.Model):

    __tablename__ = 'experiments'

    id = v.db.Column(v.db.Integer, primary_key=True)
    idu = v.db.Column(
        v.db.Integer,
        v.db.ForeignKey('users.id'),
    )
    alg_name = v.db.Column(
        v.db.String(64),
        v.db.ForeignKey('algorithms.alg_name'),
    )
    alg_config = v.db.Column(v.db.Text)
    exp_config = v.db.Column(v.db.Text)
    filter_name = v.db.Column(
        v.db.String(64),
        v.db.ForeignKey('filters.filter_name'),
        nullable=True
    )
    filter_config = v.db.Column(v.db.Text, nullable=True)
    data = v.db.Column(v.db.String(128))
    result = v.db.Column(v.db.Text, nullable=True)
    starttime = v.db.Column(v.db.Integer)
    endtime = v.db.Column(v.db.Integer, nullable=True)
    state = v.db.Column(v.db.Integer)

    def __init__(self, idu, alg_name, alg_config, exp_config,
                 filter_name, filter_config, data, result,
                 starttime, endtime, state):
        """Experiment constructor.

        Arguments:
            idu {integer} -- User who lauch experiment.
            alg_name {string} -- Experiment's algorithm name.
            alg_config {string} -- Experiment's algorithm configuration.
            data {string} -- Experiment data.
            result {string} -- Experiment result.
            starttime {integer} -- Experiment start timestamp.
            endtime {integer} -- Experiment end timestamp.
            state {integer} -- State of experiment.
                               (0. Execution, 1. completed, 2. Error)
        """
        self.idu = idu
        self.alg_name = alg_name
        self.alg_config = alg_config
        self.exp_config = exp_config
        self.filter_name = filter_name
        self.filter_config = filter_config
        self.data = data
        self.result = result
        self.starttime = starttime
        self.endtime = endtime
        self.state = state

    def to_dict(self):
        """Experiment to dict

        Returns:
            dict -- dict with keys and values from Experiment Object.
        """
        filter_ = get_filter_by_name(self.filter_name)
        if filter_ is not None:
            filter_ = filter_.to_dict()
        return {"id": self.id, "idu": self.idu,
                "alg": get_algorithm_by_name(self.alg_name).to_dict(),
                "alg_config": self.alg_config, "exp_config": self.exp_config,
                "filter": filter_,
                "filter_config": self.filter_config,
                "data": self.data,
                "result": self.result, "starttime": self.starttime,
                "endtime": self.endtime}

    def web_name(self):
        return get_algorithm_by_name(self.alg_name).web_name


class Country(v.db.Model):
    __tablename__ = 'countries'
    name = v.db.Column(v.db.String(64), nullable=False)
    alpha_2 = v.db.Column(v.db.String(64), primary_key=True)
    alpha_3 = v.db.Column(v.db.String(64), nullable=False)
    numeric = v.db.Column(v.db.Integer, nullable=False)
    longitude = v.db.Column(v.db.Float, nullable=False)
    latitude = v.db.Column(v.db.Float, nullable=False)

    def __init__(self, name, alpha_2, alpha_3, numeric, longitude, latitude):
      self.name = name
      self.alpha_2 = alpha_2
      self.alpha_3 = alpha_3
      self.numeric = numeric
      self.longitude = longitude
      self.latitude = latitude

    def to_dict(self):
        return {
            "name": self.name,
            "alpha_2": self.alpha_2,
            "alpha_3": self.alpha_3,
            "numeric": self.numeric,
            "longitude": self.longitude,
            "latitude": self.latitude
        }
