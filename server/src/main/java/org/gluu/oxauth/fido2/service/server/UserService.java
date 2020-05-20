/*
 * oxAuth is available under the MIT License (2008). See http://opensource.org/licenses/MIT for full text.
 *
 * Copyright (c) 2014, Gluu
 */

package org.gluu.oxauth.fido2.service.server;

import java.util.List;

import javax.enterprise.context.ApplicationScoped;
import javax.inject.Inject;

import org.gluu.oxauth.model.config.StaticConfiguration;

/**
 * Provides operations with users.
 *
 * @author Yuriy Movchan
 * @version @version May 20, 2020
 */
@ApplicationScoped
public class UserService extends org.gluu.oxauth.service.common.UserService {

	public static final String[] USER_OBJECT_CLASSES = new String[] { "gluuPerson" };

    @Inject
    private StaticConfiguration staticConfiguration;

    @Inject
    private AppConfiguration appConfiguration;

    @Override
	protected List<String> getPersonCustomObjectClassList() {
		return appConfiguration.getPersonCustomObjectClassList();
	}

    @Override
	protected String getPeopleBaseDn() {
		return staticConfiguration.getBaseDn().getPeople();
	}

}
